import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.security import encrypt_pii, decrypt_pii

class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    apaar_id = Column(String(12), unique=False, index=True, nullable=False)  # 12 digits, indexed (can be cross-flagged)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    program_branch_id = Column(String(36), ForeignKey("program_branches.id", ondelete="SET NULL"), nullable=True)

    # PII Encrypted at rest (AES-256-GCM)
    name_encrypted = Column(Text, nullable=False)
    dob_encrypted = Column(Text, nullable=False)
    
    # Non-sensitive searchable / demographic fields
    gender = Column(String(20), nullable=False)  # Male, Female, Other
    program = Column(String(50), nullable=False)  # B.Tech, M.Tech, MCA, etc.
    branch = Column(String(150), nullable=False)  # Computer Science, Mechanical, etc.
    year_of_study = Column(Integer, default=1, nullable=False)
    admission_date = Column(Date, nullable=False)
    quota_type = Column(String(50), default="Merit", nullable=False)  # Merit, Management, NRI, Supernumerary
    category = Column(String(50), default="General", nullable=False)  # General, OBC, SC, ST, EWS
    
    # Quota & International flags
    is_supernumerary = Column(Boolean, default=False, nullable=False)
    is_nri = Column(Boolean, default=False, nullable=False)
    is_oci = Column(Boolean, default=False, nullable=False)
    is_foreign_national = Column(Boolean, default=False, nullable=False)
    
    # Document Hash (SHA-256 for tampering detection)
    document_hash = Column(String(64), nullable=False)
    
    # Verification status
    verification_status = Column(String(50), default="VALIDATED", nullable=False)  # PENDING, VALIDATED, FLAGGED, VERIFIED
    
    # Plaintext cache for fast demo rendering (still protected by RBAC in API)
    cached_name = Column(String(255), nullable=True)
    cached_dob = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    institution = relationship("Institution", back_populates="students")
    flags = relationship("ValidationFlag", back_populates="student", cascade="all, delete-orphan")

    def get_decrypted_name(self) -> str:
        if self.cached_name:
            return self.cached_name
        decrypted = decrypt_pii(self.name_encrypted)
        return decrypted or "Unknown"

    def get_decrypted_dob(self) -> Optional[date]:
        if self.cached_dob:
            return self.cached_dob
        decrypted_str = decrypt_pii(self.dob_encrypted)
        if decrypted_str:
            try:
                return datetime.strptime(decrypted_str, "%Y-%m-%d").date()
            except Exception:
                return None
        return None
