from datetime import datetime

from sqlalchemy import Column, DateTime, JSON, String, Text

from app.database import Base


class DocumentJob(Base):
    __tablename__ = "document_jobs"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    message = Column(String, nullable=False, default="Queued for processing")
    file_path = Column(String, nullable=False)
    result_text = Column(Text, nullable=True)
    result_entities = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
