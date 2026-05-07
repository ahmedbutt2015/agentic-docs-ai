import time
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import UPLOAD_DIR
from app.database import SessionLocal, init_db
from app.models import DocumentJob
from app.schemas import (
    DashboardResponse,
    RecentJobResponse,
    ResultResponse,
    SearchHitResponse,
    SearchResponse,
    StatusResponse,
    UploadResponse,
)
from app.services import embedder, vector_store
from app.services.chunker import chunk_extraction
from app.services.ocr import build_result_payload, extract_document_data, run_extraction

app = FastAPI(
    title="Regulus AI Backend",
    description="Core backend endpoints for document ingestion, status, and result retrieval.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event() -> None:
    init_db()


def process_document(job_id: str, file_path: Path) -> None:
    db = SessionLocal()
    try:
        job = db.get(DocumentJob, job_id)
        if job is None:
            return

        job.status = "processing"
        job.message = "Extracting document text and metadata"
        db.commit()

        time.sleep(1)
        result = extract_document_data(file_path, filename=job.filename, uploaded_at=job.created_at)

        job.result_text = result["text"]
        job.result_entities = result["entities"]
        job.message = "Chunking and embedding document"
        db.commit()

        chunks_indexed = 0
        try:
            extraction = run_extraction(file_path)
            chunks = chunk_extraction(
                extraction,
                doc_id=job_id,
                source_filename=job.filename,
            )
            if chunks:
                embeddings = embedder.embed_texts([chunk["text"] for chunk in chunks])
                chunks_indexed = vector_store.replace_chunks_for_job(db, job_id, chunks, embeddings)
        except Exception as exc:
            job.status = "completed"
            job.message = f"Document data is ready (embedding skipped: {exc.__class__.__name__})"
            db.commit()
            return

        job.status = "completed"
        if chunks_indexed:
            job.message = f"Document data is ready ({chunks_indexed} chunks indexed)"
        else:
            job.message = "Document data is ready (no chunks to index)"
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "regulus-ai-backend"}


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    job_id = str(uuid4())
    target_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    content = await file.read()
    target_path.write_bytes(content)

    job = DocumentJob(
        id=job_id,
        filename=file.filename,
        status="pending",
        message="Queued for processing",
        file_path=str(target_path),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_document, job_id, target_path)
    return UploadResponse(id=job_id, status="pending", filename=file.filename)


@app.get("/status/{job_id}", response_model=StatusResponse)
def get_status(job_id: str, db: Session = Depends(get_db)) -> StatusResponse:
    job = db.get(DocumentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(
        id=job_id,
        status=job.status,
        message=job.message,
        filename=job.filename,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@app.get("/result/{job_id}", response_model=ResultResponse)
def get_result(job_id: str, db: Session = Depends(get_db)) -> ResultResponse:
    job = db.get(DocumentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result_data = None
    if job.result_text is not None or job.result_entities is not None:
        result_data = build_result_payload(
            file_path=Path(job.file_path),
            filename=job.filename,
            uploaded_at=job.created_at,
            processed_at=job.updated_at,
            text=job.result_text,
            entities=job.result_entities,
        )

    return ResultResponse(
        id=job_id,
        status=job.status,
        message=job.message,
        filename=job.filename,
        created_at=job.created_at,
        updated_at=job.updated_at,
        result=result_data,
    )


@app.get("/search", response_model=SearchResponse)
def search_chunks(
    q: str = Query(..., min_length=1, description="Free-text query"),
    limit: int = Query(5, ge=1, le=50),
    job_id: str = Query(None, description="Optional: restrict search to one document"),
    db: Session = Depends(get_db),
) -> SearchResponse:
    query_embedding = embedder.embed_text(q)
    hits = vector_store.search_similar_chunks(db, query_embedding, limit=limit, job_id=job_id)
    return SearchResponse(
        query=q,
        hits=[
            SearchHitResponse(
                chunk_id=hit["chunk_id"],
                job_id=hit["job_id"],
                page_number=hit["page_number"],
                chunk_index=hit["chunk_index"],
                text=hit["text"],
                source_filename=hit["source_filename"],
                score=hit["score"],
            )
            for hit in hits
        ],
    )


@app.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    jobs = db.query(DocumentJob).order_by(desc(DocumentJob.created_at)).all()
    completed_jobs = [job for job in jobs if job.status == "completed"]
    processing_jobs = [job for job in jobs if job.status == "processing"]
    pending_jobs = [job for job in jobs if job.status == "pending"]
    failed_jobs = [job for job in jobs if job.status == "failed"]

    recent_jobs = []
    score_values = []
    total_issues = 0

    for job in jobs[:5]:
        score = None
        issue_count = 0

        if job.result_text is not None or job.result_entities is not None:
            payload = build_result_payload(
                file_path=Path(job.file_path),
                filename=job.filename,
                uploaded_at=job.created_at,
                processed_at=job.updated_at,
                text=job.result_text,
                entities=job.result_entities,
            )
            score = payload["score"]["value"]
            issue_count = len(payload["issues"])

        recent_jobs.append(
            RecentJobResponse(
                id=job.id,
                filename=job.filename,
                status=job.status,
                message=job.message,
                created_at=job.created_at,
                updated_at=job.updated_at,
                score=score,
                issue_count=issue_count,
            )
        )

    for job in completed_jobs:
        payload = build_result_payload(
            file_path=Path(job.file_path),
            filename=job.filename,
            uploaded_at=job.created_at,
            processed_at=job.updated_at,
            text=job.result_text,
            entities=job.result_entities,
        )
        score_values.append(payload["score"]["value"])
        total_issues += len(payload["issues"])

    average_score = round(sum(score_values) / len(score_values)) if score_values else 0

    return DashboardResponse(
        total_jobs=len(jobs),
        completed_jobs=len(completed_jobs),
        processing_jobs=len(processing_jobs),
        pending_jobs=len(pending_jobs),
        failed_jobs=len(failed_jobs),
        total_issues=total_issues,
        average_score=average_score,
        recent_jobs=recent_jobs,
    )
