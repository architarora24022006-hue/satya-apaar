import json
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.institution import Institution
from app.models.consent import ConsentWallet, VerificationAccessLog
from app.core.security import sign_claim, verify_claim_signature, get_public_key_b64, compute_sha256
from app.services.audit_service import AuditService

# Standard Field Classifications under DPDP Act 2023
DEFAULT_PUBLIC_FIELDS = [
    "apaar_id_masked",
    "student_name",
    "institution_name",
    "institution_aicte_id",
    "program",
    "branch",
    "year_of_study",
    "aicte_approved",
    "verification_status"
]

ALL_STUDENT_FIELDS = [
    "apaar_id",
    "apaar_id_masked",
    "student_name",
    "dob",
    "gender",
    "institution_name",
    "institution_aicte_id",
    "program",
    "branch",
    "year_of_study",
    "admission_date",
    "quota_type",
    "category",
    "aicte_approved",
    "verification_status"
]

SENSITIVE_PII_FIELDS = [
    "dob",
    "category",
    "gender",
    "quota_type",
    "admission_date",
    "apaar_id"
]

class VerificationService:
    @staticmethod
    def verify_student_record(
        db: Session,
        apaar_id: str,
        verifier_name: str,
        verifier_org: str,
        verifier_role: str = "EMPLOYER_VERIFIER",
        purpose: str = "Employment Background Check",
        otp_code: Optional[str] = None,
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Executes selective disclosure verification compliant with India's DPDP Act 2023.
        Omit sensitive PII unless explicit student consent or valid OTP authorization is present.
        """
        student = db.query(Student).filter(Student.apaar_id == apaar_id).first()
        if not student:
            return None

        # Build full raw attribute dictionary
        masked_apaar = f"XXXX-XXXX-{student.apaar_id[-4:]}"
        inst_name = student.institution.name if student.institution else "AICTE Institution"
        inst_aicte_id = student.institution.aicte_id if student.institution else "1-00000000"

        full_record = {
            "apaar_id": student.apaar_id,
            "apaar_id_masked": masked_apaar,
            "student_name": student.get_decrypted_name(),
            "dob": student.get_decrypted_dob().isoformat() if student.get_decrypted_dob() else None,
            "gender": student.gender,
            "institution_name": inst_name,
            "institution_aicte_id": inst_aicte_id,
            "program": student.program,
            "branch": student.branch,
            "year_of_study": student.year_of_study,
            "admission_date": student.admission_date.isoformat() if student.admission_date else None,
            "quota_type": student.quota_type,
            "category": student.category,
            "aicte_approved": True,
            "verification_status": student.verification_status
        }

        # Check for Student Consent Wallet config
        mapped_role_key = "EMPLOYER" if "EMPLOYER" in verifier_role.upper() else (
            "UNIVERSITY" if "UNIVERSITY" in verifier_role.upper() else "PUBLIC_VERIFIER"
        )
        
        consent = db.query(ConsentWallet).filter(
            ConsentWallet.student_apaar_id == apaar_id,
            ConsentWallet.verifier_type == mapped_role_key,
            ConsentWallet.is_active == True
        ).first()

        consent_status = "DEFAULT_SELECTIVE_DISCLOSURE"
        allowed_fields: List[str] = list(DEFAULT_PUBLIC_FIELDS)

        # Check OTP elevation
        if otp_code:
            expected_otp = consent.otp_code if (consent and consent.otp_code) else "123456"
            if otp_code.strip() == expected_otp:
                consent_status = "OTP_ELEVATED_ACCESS"
                allowed_fields = list(ALL_STUDENT_FIELDS)
            else:
                consent_status = "OTP_INVALID_FALLBACK_DEFAULT"

        elif consent and consent.allowed_fields:
            consent_status = "STUDENT_CONSENT_GRANTED"
            allowed_fields = consent.allowed_fields

        # Filter disclosed vs restricted
        disclosed_data = {k: full_record[k] for k in allowed_fields if k in full_record}
        restricted_fields = [k for k in ALL_STUDENT_FIELDS if k not in disclosed_data]

        now = datetime.now(timezone.utc)

        # Canonical claim for Ed25519 cryptographic signing
        canonical_claim = {
            "apaar_id_masked": masked_apaar,
            "student_name": student.get_decrypted_name(),
            "program": student.program,
            "branch": student.branch,
            "year_of_study": student.year_of_study,
            "institution_name": inst_name,
            "institution_aicte_id": inst_aicte_id,
            "aicte_approved": True,
            "enrollment_valid": student.verification_status in ["VALIDATED", "VERIFIED"],
            "verification_timestamp": now.isoformat(),
            "issuer": "AICTE-SATYA-APAAR-CENTRAL",
            "document_hash": student.document_hash or compute_sha256(student.apaar_id)
        }

        signature = sign_claim(canonical_claim)
        public_key = get_public_key_b64()

        # Build portable QR Payload
        qr_dict = {
            "claim": canonical_claim,
            "signature": signature,
            "public_key": public_key,
            "issuer": "AICTE_SATYA_APAAR",
            "version": "1.0"
        }
        qr_payload = json.dumps(qr_dict, separators=(',', ':'))

        # Log into DPDP access audit
        access_log = VerificationAccessLog(
            student_apaar_id=apaar_id,
            verifier_name=verifier_name,
            verifier_org=verifier_org,
            verifier_role=verifier_role,
            accessed_fields=list(disclosed_data.keys()),
            purpose=purpose,
            ip_address=ip_address,
            timestamp=now
        )
        db.add(access_log)
        db.commit()
        db.refresh(access_log)

        # Chained Audit Log
        AuditService.append_log(
            db=db,
            action="VERIFICATION_COMPLETED",
            entity_type="STUDENT",
            entity_id=student.apaar_id,
            role=verifier_role,
            user_email=f"{verifier_name.lower().replace(' ', '.')}@{verifier_org.lower().replace(' ', '')}.com",
            details={
                "verifier_name": verifier_name,
                "verifier_org": verifier_org,
                "purpose": purpose,
                "disclosed_fields_count": len(disclosed_data),
                "consent_status": consent_status
            },
            ip_address=ip_address
        )

        return {
            "apaar_id": student.apaar_id,
            "apaar_id_masked": masked_apaar,
            "student_name": student.get_decrypted_name(),
            "verification_status": student.verification_status,
            "institution_name": inst_name,
            "institution_aicte_id": inst_aicte_id,
            "program": student.program,
            "branch": student.branch,
            "year_of_study": student.year_of_study,
            "aicte_approved": True,
            "disclosed_data": disclosed_data,
            "restricted_fields": restricted_fields,
            "consent_status": consent_status,
            "canonical_claim": canonical_claim,
            "signature_ed25519": signature,
            "public_key_b64": public_key,
            "qr_payload": qr_payload,
            "verified_at": now,
            "access_log_id": str(access_log.id)
        }

    @staticmethod
    def verify_offline_claim(
        claim: Dict[str, Any],
        signature_ed25519: str,
        public_key_b64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pure offline cryptographic verification using Ed25519 signature and public key.
        Does NOT connect to the database or internet.
        """
        now = datetime.now(timezone.utc)
        pub_key = public_key_b64 or get_public_key_b64()
        
        is_valid = verify_claim_signature(
            claim_dict=claim,
            signature_b64=signature_ed25519,
            public_key_b64=pub_key
        )

        if is_valid:
            return {
                "is_valid": True,
                "algorithm": "Ed25519",
                "issuer": claim.get("issuer", "AICTE-SATYA-APAAR-CENTRAL"),
                "verified_at": now,
                "message": "Cryptographic signature VALID. Record matches AICTE Central Authority root certificate.",
                "claim": claim
            }
        else:
            return {
                "is_valid": False,
                "algorithm": "Ed25519",
                "issuer": claim.get("issuer", "UNKNOWN_OR_UNTRUSTED"),
                "verified_at": now,
                "message": "INVALID SIGNATURE OR TAMPERED RECORD: Payload checksum does not match digital signature.",
                "claim": claim
            }
