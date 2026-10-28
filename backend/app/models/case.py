import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = Column(String(50), unique=True, index=True, nullable=False)  # CASE-2026-0001
    title = Column(String(255), nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    clash_institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    related_student_apaar = Column(String(12), nullable=True, index=True)

    status = Column(String(50), default="OPEN", nullable=False)  # OPEN, IN_REVIEW, PENDING_APPROVAL, RESOLVED, ESCALATED
    priority = Column(String(20), default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    
    opened_by_type = Column(String(50), default="SENTINEL", nullable=False)  # SYSTEM, SENTINEL, OFFICER
    description = Column(Text, nullable=False)
    action_draft = Column(Text, nullable=True)  # Drafted notice / sanction by Sentinel
    resolution_notes = Column(Text, nullable=True)
    
    evidence_pack = Column(JSON, nullable=True)  # Attached stats, match confidence, audit snapshots

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
