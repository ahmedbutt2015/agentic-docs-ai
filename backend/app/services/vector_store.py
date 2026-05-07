from typing import Any, Dict, List

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import DocumentChunk


def replace_chunks_for_job(
    db: Session,
    job_id: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"chunk/embedding length mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
        )

    db.execute(delete(DocumentChunk).where(DocumentChunk.job_id == job_id))

    for chunk, embedding in zip(chunks, embeddings):
        db.add(
            DocumentChunk(
                id=chunk["chunk_id"],
                job_id=job_id,
                page_number=chunk["page_number"],
                chunk_index=chunk["chunk_index"],
                text=chunk["text"],
                token_count=chunk["token_count"],
                char_start=chunk.get("char_start"),
                char_end=chunk.get("char_end"),
                source_filename=chunk.get("source_filename"),
                embedding=embedding,
            )
        )

    db.commit()
    return len(chunks)


def search_similar_chunks(
    db: Session,
    query_embedding: List[float],
    limit: int = 5,
    job_id: str = None,
) -> List[Dict[str, Any]]:
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    stmt = select(DocumentChunk, distance.label("distance"))
    if job_id is not None:
        stmt = stmt.where(DocumentChunk.job_id == job_id)
    stmt = stmt.order_by(distance).limit(limit)

    rows = db.execute(stmt).all()
    return [
        {
            "chunk_id": row.DocumentChunk.id,
            "job_id": row.DocumentChunk.job_id,
            "page_number": row.DocumentChunk.page_number,
            "chunk_index": row.DocumentChunk.chunk_index,
            "text": row.DocumentChunk.text,
            "source_filename": row.DocumentChunk.source_filename,
            "score": float(1.0 - row.distance),
        }
        for row in rows
    ]


def count_chunks_for_job(db: Session, job_id: str) -> int:
    return db.scalar(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.job_id == job_id)
    ) or 0
