import time
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import SessionLocal, init_db
from app.models import DocumentJob
from app.schemas import UploadResponse, StatusResponse, ResultResponse
from app.services.ocr import extract_document_data

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
        job.message = "Running OCR and metadata extraction"
        db.commit()

        time.sleep(1)
        result = extract_document_data(file_path)

        job.result_text = result["text"]
        job.result_entities = result["entities"]
        job.status = "completed"
        job.message = "Processing complete"
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

    background_tasks.add_task(process_document, job_id, target_path)
    return UploadResponse(id=job_id, status="pending")


@app.get("/status/{job_id}", response_model=StatusResponse)
def get_status(job_id: str, db: Session = Depends(get_db)) -> StatusResponse:
    job = db.get(DocumentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(id=job_id, status=job.status, message=job.message)


@app.get("/result/{job_id}", response_model=ResultResponse)
def get_result(job_id: str, db: Session = Depends(get_db)) -> ResultResponse:
    job = db.get(DocumentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result_data = None
    if job.result_text is not None or job.result_entities is not None:
        result_data = {
            "text": job.result_text or "",
            "entities": job.result_entities or {},
        }

    return ResultResponse(
        id=job_id,
        status=job.status,
        message=job.message,
        result=result_data,
    )
