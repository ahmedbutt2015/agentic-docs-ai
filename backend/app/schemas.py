from typing import Any, Dict, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: str
    status: str


class StatusResponse(BaseModel):
    id: str
    status: str
    message: str


class OCRResult(BaseModel):
    text: str
    entities: Dict[str, Any]


class ResultResponse(BaseModel):
    id: str
    status: str
    message: str
    result: Optional[OCRResult] = None
