from typing import Any, Dict, Optional

jobs: Dict[str, Dict[str, Any]] = {}


def create_job(job_id: str, filename: str) -> Dict[str, Any]:
    jobs[job_id] = {
        "id": job_id,
        "filename": filename,
        "status": "pending",
        "message": "Queued for processing",
        "result": None,
    }
    return jobs[job_id]


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return jobs.get(job_id)


def update_job_status(job_id: str, status: str, message: str) -> None:
    if job_id in jobs:
        jobs[job_id]["status"] = status
        jobs[job_id]["message"] = message


def set_job_result(job_id: str, result: Dict[str, Any]) -> None:
    if job_id in jobs:
        jobs[job_id]["result"] = result
