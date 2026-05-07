from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.config import EMBEDDING_DIMENSIONS
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
    result_compliance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship(
        "DocumentChunk",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("document_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    source_filename = Column(String, nullable=True)
    embedding = Column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("DocumentJob", back_populates="chunks")


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String, nullable=False, unique=True, index=True)
    framework = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    check = Column(Text, nullable=False)
    severity = Column(String, nullable=False, default="Medium")
    is_default = Column(Boolean, nullable=False, default=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
