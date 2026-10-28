import re
from typing import Any, Dict, List, Tuple

CANONICAL_SCHEMA = {
    "apaar_id": {
        "label": "12-Digit APAAR ID",
        "aliases": ["apaar", "apaar_id", "apaar_no", "apaar_number", "student_apaar", "abc_id", "student_id", "uid"],
        "required": True
    },
    "name": {
        "label": "Student Full Name",
        "aliases": ["name", "student_name", "candidate_name", "full_name", "applicant_name", "student"],
        "required": True
    },
    "dob": {
        "label": "Date of Birth",
        "aliases": ["dob", "date_of_birth", "birth_date", "d_o_b", "birthdate"],
        "required": True
    },
    "gender": {
        "label": "Gender",
        "aliases": ["gender", "sex", "m_f"],
        "required": True
    },
    "program": {
        "label": "Academic Program (UG/PG)",
        "aliases": ["program", "course", "degree", "prog", "level"],
        "required": True
    },
    "branch": {
        "label": "Branch / Discipline",
        "aliases": ["branch", "specialization", "stream", "discipline", "department", "field"],
        "required": True
    },
    "year_of_study": {
        "label": "Year of Study",
        "aliases": ["year", "year_of_study", "current_year", "semester_year", "class_year"],
        "required": False
    },
    "admission_date": {
        "label": "Admission Date",
        "aliases": ["admission_date", "date_of_admission", "enrolment_date", "joining_date", "doa"],
        "required": True
    },
    "quota_type": {
        "label": "Admission Quota",
        "aliases": ["quota", "quota_type", "admission_quota", "seat_type", "allotment_category"],
        "required": False
    },
    "category": {
        "label": "Social Category (General/OBC/SC/ST)",
        "aliases": ["category", "caste_category", "social_category", "reservation_category", "caste"],
        "required": False
    },
    "is_supernumerary": {
        "label": "Supernumerary Flag",
        "aliases": ["supernumerary", "is_supernumerary", "sn_seat", "tfw_flag", "extra_seat"],
        "required": False
    },
    "is_nri": {
        "label": "NRI Flag",
        "aliases": ["nri", "is_nri", "nri_quota", "nri_sponsored"],
        "required": False
    },
    "is_oci": {
        "label": "OCI Flag",
        "aliases": ["oci", "is_oci", "overseas_citizen"],
        "required": False
    },
    "is_foreign_national": {
        "label": "Foreign National Flag",
        "aliases": ["foreign_national", "is_foreign_national", "fn_quota", "international_student"],
        "required": False
    }
}

class ColumnMapper:
    @staticmethod
    def normalize_header(header: str) -> str:
        """Strips special characters, spaces, and lowers case for fuzzy matching."""
        return re.sub(r"[^a-z0-9]", "_", str(header).lower().strip()).strip("_")

    @classmethod
    def auto_map_headers(cls, detected_headers: List[str]) -> Dict[str, Any]:
        """
        Maps raw input column headers to canonical SATYA-APAAR fields.
        Returns:
            {
               "mapping": { "raw_header": "canonical_field" },
               "confidence": { "raw_header": float },
               "unmapped": [ "header" ],
               "missing_required": [ "canonical_field" ]
            }
        """
        mapping: Dict[str, str] = {}
        confidences: Dict[str, float] = {}
        used_canonical = set()

        for raw_h in detected_headers:
            clean_h = cls.normalize_header(raw_h)
            best_match = None
            best_score = 0.0

            for canonical_key, meta in CANONICAL_SCHEMA.items():
                if canonical_key in used_canonical:
                    continue

                # Exact match
                if clean_h == canonical_key:
                    best_match = canonical_key
                    best_score = 1.0
                    break

                # Alias exact match
                if clean_h in meta["aliases"]:
                    best_match = canonical_key
                    best_score = 0.95
                    break

                # Substring match
                for alias in meta["aliases"]:
                    if alias in clean_h or clean_h in alias:
                        score = len(alias) / max(len(clean_h), len(alias)) * 0.9
                        if score > best_score:
                            best_score = score
                            best_match = canonical_key

            if best_match and best_score >= 0.60:
                mapping[raw_h] = best_match
                confidences[raw_h] = round(best_score, 2)
                used_canonical.add(best_match)

        unmapped = [h for h in detected_headers if h not in mapping]
        missing_required = [
            k for k, v in CANONICAL_SCHEMA.items()
            if v["required"] and k not in used_canonical
        ]

        return {
            "mapping": mapping,
            "confidence": confidences,
            "unmapped": unmapped,
            "missing_required": missing_required,
            "canonical_schema": {k: v["label"] for k, v in CANONICAL_SCHEMA.items()}
        }

    @classmethod
    def transform_row(cls, raw_row: Dict[str, Any], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Transforms a raw uploaded dictionary row into canonical schema format."""
        canonical_record: Dict[str, Any] = {}
        for raw_col, raw_val in raw_row.items():
            canonical_field = column_mapping.get(raw_col)
            if canonical_field:
                val = str(raw_val).strip() if raw_val is not None else ""
                # Parse boolean flags
                if canonical_field in ["is_supernumerary", "is_nri", "is_oci", "is_foreign_national"]:
                    canonical_record[canonical_field] = val.lower() in ["true", "1", "yes", "y", "t"]
                elif canonical_field == "year_of_study":
                    try:
                        canonical_record[canonical_field] = int(val)
                    except ValueError:
                        canonical_record[canonical_field] = 1
                else:
                    canonical_record[canonical_field] = val

        return canonical_record
