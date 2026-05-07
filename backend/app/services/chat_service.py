from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.llm import chat_completion
from app.config import ANTHROPIC_MODEL, LLM_MODEL, LLM_PROVIDER
from app.services import embedder, pipeline_log, vector_store


SYSTEM_PROMPT = (
    "You are a document analyst helping the user understand and reason about their uploaded "
    "documents.\n"
    "- Use ONLY the provided document context. Do not invent facts.\n"
    "- If the answer is not in the context, say \"I couldn't find that in the document(s).\"\n"
    "- When citing, mention the page number — e.g. \"(page 3 of contract.pdf)\".\n"
    "- Keep answers concise: 1–3 sentences usually, longer only if the user asks for detail."
)

MAX_HISTORY_TURNS = 6
MAX_PREVIEW_CHARS = 280


def _build_user_message(question: str, citations: List[Dict[str, Any]]) -> str:
    blocks = []
    for index, citation in enumerate(citations, start=1):
        blocks.append(
            f"[Source {index}: {citation['source_filename'] or 'unknown'}, "
            f"page {citation['page_number']}, similarity {citation['score']:.2f}]\n"
            f"{citation['text']}"
        )
    context_text = "\n\n---\n\n".join(blocks) if blocks else "(no relevant context retrieved)"
    return (
        f"DOCUMENT CONTEXT:\n{context_text}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the context above. Cite source numbers like (Source 1) when helpful."
    )


def chat_about_documents(
    db: Session,
    question: str,
    job_id: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    limit: int = 6,
) -> Dict[str, Any]:
    pipeline_log.section(
        "CHAT",
        scope=job_id[:8] if job_id else "all",
        q_chars=len(question),
        history=len(history or []),
    )

    with pipeline_log.timed() as timer:
        question_embedding = embedder.embed_text(question)
    pipeline_log.line(f"query embedding in {timer.fmt()}")

    with pipeline_log.timed() as timer:
        hits = vector_store.search_similar_chunks(
            db, question_embedding, limit=limit, job_id=job_id
        )
    pipeline_log.line(f"retrieved {len(hits)} chunks in {timer.fmt()}")

    citations: List[Dict[str, Any]] = [
        {
            "chunk_id": hit["chunk_id"],
            "job_id": hit["job_id"],
            "page_number": hit["page_number"],
            "chunk_index": hit["chunk_index"],
            "source_filename": hit["source_filename"],
            "score": hit["score"],
            "text": hit["text"],
            "preview": hit["text"][:MAX_PREVIEW_CHARS],
        }
        for hit in hits
    ]

    if not citations:
        return {
            "answer": "I couldn't find any relevant content in the indexed documents to answer that.",
            "citations": [],
        }

    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for turn in history[-MAX_HISTORY_TURNS:]:
            role = turn.get("role")
            content = turn.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": _build_user_message(question, citations)})

    model = ANTHROPIC_MODEL if LLM_PROVIDER == "anthropic" else LLM_MODEL
    pipeline_log.line(f"calling {LLM_PROVIDER}/{model} with {len(messages)} messages")

    try:
        with pipeline_log.timed() as timer:
            answer = chat_completion(
                messages,
                provider=LLM_PROVIDER,
                model=model,
                max_tokens=600,
                temperature=0.2,
            )
        pipeline_log.line(f"got {len(answer)} chars in {timer.fmt()}")
    except Exception as exc:
        pipeline_log.line(f"chat LLM call failed: {exc.__class__.__name__}: {exc}")
        return {
            "answer": (
                "The chat model failed to respond. Check the backend logs for the LLM error and "
                "try again."
            ),
            "citations": [
                {key: citation[key] for key in citation if key != "text"}
                for citation in citations
            ],
        }

    return {
        "answer": (answer or "").strip(),
        "citations": [
            {key: citation[key] for key in citation if key != "text"}
            for citation in citations
        ],
    }
