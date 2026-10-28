from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: str
    sequence_number: int
    timestamp: datetime
    user_email: Optional[str] = None
    role: str
    ip_address: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    payload_hash: str
    previous_hash: str
    current_hash: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AuditIntegrityCheckResult(BaseModel):
    total_records_checked: int
    chain_valid: bool
    broken_at_sequence: Optional[int] = None
    message: str
    latest_block_hash: str
    checked_at: datetime
