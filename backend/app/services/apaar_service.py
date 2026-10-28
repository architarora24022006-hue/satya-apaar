from typing import Any, Dict, Optional, Tuple
import re

# Verhoeff algorithm multiplication and permutation tables for 12-digit Indian national identifiers (Aadhaar/APAAR)
d_table = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

p_table = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

inv_table = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

class ApaarService:
    """
    APAAR (Automated Permanent Academic Account Registry) Service Interface.
    Production architecture with swappable backend adapter (Mocked for Demo, 
    designed for official DigiLocker/ABC/APAAR API integration).
    """

    @staticmethod
    def validate_format_and_checksum(apaar_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validates 12-digit format and Verhoeff checksum algorithm.
        Returns: (is_valid, error_reason)
        """
        clean_id = str(apaar_id).strip().replace(" ", "").replace("-", "")
        
        if not re.match(r"^\d{12}$", clean_id):
            return False, f"APAAR ID must be exactly 12 digits (found: '{apaar_id}')"
        
        # Verify Verhoeff checksum
        c = 0
        inverted_digits = [int(x) for x in reversed(clean_id)]
        for i, digit in enumerate(inverted_digits):
            c = d_table[c][p_table[i % 8][digit]]
            
        if c != 0:
            return False, f"Invalid Verhoeff checksum for APAAR ID '{clean_id}'"
            
        return True, None

    @staticmethod
    def generate_valid_apaar(base_number_str: str) -> str:
        """Helper to generate a checksum-valid 12-digit APAAR ID from 11 digits."""
        base = base_number_str.zfill(11)[:11]
        c = 0
        inverted_digits = [int(x) for x in reversed(base)]
        for i, digit in enumerate(inverted_digits):
            c = d_table[c][p_table[(i + 1) % 8][digit]]
        check_digit = inv_table[c]
        return f"{base}{check_digit}"

    @classmethod
    async def lookup_apaar_registry(cls, apaar_id: str) -> Dict[str, Any]:
        """
        External APAAR/ABC Registry verification lookup.
        In demo mode, simulates the official API response.
        """
        is_valid, error = cls.validate_format_and_checksum(apaar_id)
        if not is_valid:
            return {
                "verified": False,
                "apaar_id": apaar_id,
                "error": error,
                "status": "INVALID_CHECKSUM",
                "source": "APAAR_GATEWAY_MOCK"
            }
        
        return {
            "verified": True,
            "apaar_id": apaar_id,
            "status": "ACTIVE",
            "linked_aadhaar_ref": f"XXXX-XXXX-{apaar_id[-4:]}",
            "abc_account_id": f"ABC-{apaar_id}",
            "source": "APAAR_GATEWAY_MOCK"
        }
