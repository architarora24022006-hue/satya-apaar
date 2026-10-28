import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.audit import AuditLog
from app.core.security import compute_sha256, compute_audit_hash

GENESIS_HASH = "0" * 64

class AuditService:
    @staticmethod
    def append_log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[str],
        role: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "127.0.0.1"
    ) -> AuditLog:
        """Appends a new cryptographically chained audit log entry."""
        # Find latest entry to get sequence and previous hash
        latest = db.query(AuditLog).order_by(desc(AuditLog.sequence_number)).first()
        
        sequence_number = (latest.sequence_number + 1) if latest else 1
        previous_hash = latest.current_hash if latest else GENESIS_HASH
        
        now = datetime.now(timezone.utc)
        payload_data = details or {}
        payload_hash = compute_sha256(payload_data)
        canonical_ts = now.strftime("%Y-%m-%d %H:%M:%S")
        
        current_hash = compute_audit_hash(
            sequence_number=sequence_number,
            timestamp_iso=canonical_ts,
            user_id=str(user_id or "ANONYMOUS"),
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id or ""),
            payload_hash=payload_hash,
            previous_hash=previous_hash
        )
        
        log_entry = AuditLog(
            sequence_number=sequence_number,
            timestamp=now,
            user_id=str(user_id) if user_id else None,
            user_email=user_email,
            role=role,
            ip_address=ip_address,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            current_hash=current_hash,
            details=payload_data
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def verify_chain_integrity(db: Session) -> Dict[str, Any]:
        """Validates hash-chain integrity from Genesis block to the tip."""
        logs = db.query(AuditLog).order_by(AuditLog.sequence_number.asc()).all()
        
        if not logs:
            return {
                "total_records_checked": 0,
                "chain_valid": True,
                "broken_at_sequence": None,
                "message": "Audit trail is empty (valid genesis state).",
                "latest_block_hash": GENESIS_HASH,
                "checked_at": datetime.now(timezone.utc)
            }

        expected_prev = GENESIS_HASH
        for idx, entry in enumerate(logs):
            expected_seq = idx + 1
            if entry.sequence_number != expected_seq:
                return {
                    "total_records_checked": idx,
                    "chain_valid": False,
                    "broken_at_sequence": entry.sequence_number,
                    "message": f"Sequence discontinuity detected at record #{entry.sequence_number} (expected #{expected_seq}).",
                    "latest_block_hash": entry.previous_hash,
                    "checked_at": datetime.now(timezone.utc)
                }

            if entry.previous_hash != expected_prev:
                return {
                    "total_records_checked": idx,
                    "chain_valid": False,
                    "broken_at_sequence": entry.sequence_number,
                    "message": f"Hash chain linkage broken at sequence #{entry.sequence_number}. Previous hash mismatch.",
                    "latest_block_hash": entry.previous_hash,
                    "checked_at": datetime.now(timezone.utc)
                }

            # Re-verify payload hash
            recomputed_payload_hash = compute_sha256(entry.details or {})
            if recomputed_payload_hash != entry.payload_hash:
                return {
                    "total_records_checked": idx,
                    "chain_valid": False,
                    "broken_at_sequence": entry.sequence_number,
                    "message": f"Data payload tampering detected at sequence #{entry.sequence_number}.",
                    "latest_block_hash": entry.current_hash,
                    "checked_at": datetime.now(timezone.utc)
                }

            canonical_ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            recomputed_block_hash = compute_audit_hash(
                sequence_number=entry.sequence_number,
                timestamp_iso=canonical_ts,
                user_id=str(entry.user_id or "ANONYMOUS"),
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=str(entry.entity_id or ""),
                payload_hash=entry.payload_hash,
                previous_hash=entry.previous_hash
            )

            if recomputed_block_hash != entry.current_hash:
                return {
                    "total_records_checked": idx,
                    "chain_valid": False,
                    "broken_at_sequence": entry.sequence_number,
                    "message": f"Block hash tampering detected at sequence #{entry.sequence_number}.",
                    "latest_block_hash": entry.current_hash,
                    "checked_at": datetime.now(timezone.utc)
                }

            expected_prev = entry.current_hash

        return {
            "total_records_checked": len(logs),
            "chain_valid": True,
            "broken_at_sequence": None,
            "message": f"Audit trail verified: All {len(logs)} records cryptographically secure and unbroken.",
            "latest_block_hash": expected_prev,
            "checked_at": datetime.now(timezone.utc)
        }

    @staticmethod
    def tamper_entry_for_demo(db: Session, sequence_number: int) -> bool:
        """Deliberately modifies an audit entry payload to demonstrate tamper detection in Hackathon demo."""
        entry = db.query(AuditLog).filter(AuditLog.sequence_number == sequence_number).first()
        if not entry:
            return False
        # Inject unauthorized payload change
        mutated_details = dict(entry.details or {})
        mutated_details["TAMPERED_FLAG"] = "Malicious unauthorized modification detected!"
        entry.details = mutated_details
        db.commit()
        return True

    @staticmethod
    def restore_entry_for_demo(db: Session, sequence_number: int) -> bool:
        """Restores tampered audit entry payload back to original hash-matching state."""
        entry = db.query(AuditLog).filter(AuditLog.sequence_number == sequence_number).first()
        if not entry:
            return False
        mutated_details = dict(entry.details or {})
        if "TAMPERED_FLAG" in mutated_details:
            del mutated_details["TAMPERED_FLAG"]
            entry.details = mutated_details
            db.commit()
        return True

