import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String, JSON

from app.core.database import Base

class ConsentWallet(Base):
    __tablename__ = "consent_wallets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_apaar_id = Column(String(12), index=True, nullable=False)
    verifier_type = Column(String(50), nullable=False)  # EMPLOYER, UNIVERSITY, PUBLIC_VERIFIER
    allowed_fields = Column(JSON, nullable=False)  # e.g., ["apaar_id", "name", "program", "branch", "year_of_study", "institution_name"]
    
    is_active = Column(Boolean, default=True, nullable=False)
    otp_code = Column(String(6), nullable=True)  # Simulated OTP for consent authorization
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class VerificationAccessLog(Base):
    __tablename__ = "verification_access_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_apaar_id = Column(String(12), index=True, nullable=False)
    verifier_name = Column(String(150), nullable=False)
    verifier_org = Column(String(150), nullable=False)
    verifier_role = Column(String(50), default="EMPLOYER_VERIFIER", nullable=False)
    
    accessed_fields = Column(JSON, nullable=False)
    purpose = Column(String(255), default="Employment Verification", nullable=False)
    ip_address = Column(String(50), default="127.0.0.1", nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
