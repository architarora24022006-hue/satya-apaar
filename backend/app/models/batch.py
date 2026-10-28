import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    
    total_records = Column(Integer, default=0, nullable=False)
    processed_records = Column(Integer, default=0, nullable=False)
    valid_records = Column(Integer, default=0, nullable=False)
    flagged_records = Column(Integer, default=0, nullable=False)
    
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    error_summary = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    flags = relationship("ValidationFlag", back_populates="batch", cascade="all, delete-orphan")

class ValidationFlag(Base):
    __tablename__ = "validation_flags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_batch_id = Column(String(36), ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    apaar_id = Column(String(12), nullable=True, index=True)

    rule_code = Column(String(50), nullable=False, index=True)  # e.g., APAAR_INVALID, CROSS_INST_CLASH, OVER_INTAKE, LOGICAL_CONFLICT
    severity = Column(String(20), default="HIGH", nullable=False)  # INFO, WARNING, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    fix_suggestion = Column(Text, nullable=True)
    
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String(100), nullable=True)  # SENTINEL_AUTO, USER_MANUAL, HUMAN_OFFICER
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    batch = relationship("UploadBatch", back_populates="flags")
    student = relationship("Student", back_populates="flags")
