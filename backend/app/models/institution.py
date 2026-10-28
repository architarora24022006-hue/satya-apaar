import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aicte_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    state = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)  # Northern, Southern, Western, Eastern, etc.
    type = Column(String(50), default="Govt", nullable=False)  # Govt, Autonomous, Private
    
    trust_score = Column(Float, default=95.0, nullable=False)
    approved_intake = Column(Integer, default=0, nullable=False)
    actual_enrolment = Column(Integer, default=0, nullable=False)
    supernumerary_intake = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, WARNING, LOCKED, UNDER_AUDIT
    
    contact_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", back_populates="institution", cascade="all, delete-orphan")
    programs = relationship("ProgramBranch", back_populates="institution", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="institution", cascade="all, delete-orphan")
    trust_history = relationship("InstitutionTrustHistory", back_populates="institution", cascade="all, delete-orphan")

class ProgramBranch(Base):
    __tablename__ = "program_branches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    program = Column(String(50), nullable=False)  # UG, PG, Diploma
    branch = Column(String(150), nullable=False)  # Computer Science & Engineering, etc.
    academic_year = Column(String(20), default="2025-2026", nullable=False)
    approved_intake = Column(Integer, default=60, nullable=False)
    enrolled_count = Column(Integer, default=0, nullable=False)
    supernumerary_intake = Column(Integer, default=0, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)


    institution = relationship("Institution", back_populates="programs")

class InstitutionTrustHistory(Base):
    __tablename__ = "institution_trust_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    data_quality_factor = Column(Float, default=1.0, nullable=False)
    timeliness_factor = Column(Float, default=1.0, nullable=False)
    anomaly_penalty = Column(Float, default=0.0, nullable=False)
    resolution_speed_factor = Column(Float, default=1.0, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    institution = relationship("Institution", back_populates="trust_history")
