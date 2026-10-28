import uuid
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, String, Text, JSON

from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_number = Column(BigInteger, unique=True, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    user_id = Column(String(50), nullable=True)
    user_email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False)
    ip_address = Column(String(50), default="127.0.0.1", nullable=False)
    
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(100), nullable=True)
    
    payload_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)  # SHA-256(sequence|timestamp|user|action|entity_type|entity_id|payload_hash|previous_hash)
    
    details = Column(JSON, nullable=True)
