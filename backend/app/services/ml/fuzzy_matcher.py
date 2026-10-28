from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.institution import Institution

class FuzzyDuplicateMatcher:
    """
    Cross-Institution Fuzzy Duplicate Matcher.
    Detects students registered at multiple institutions under slight name variations,
    middle initials, phonetic misspellings, or formatting discrepancies.
    """

    @classmethod
    def find_cross_institution_duplicates(
        cls, db: Session, similarity_threshold: float = 80.0, limit: int = 50
    ) -> List[Dict[str, Any]]:
        students = db.query(Student).all()
        if len(students) < 2:
            return []

        # Prepare decrypted lightweight records
        records = []
        for s in students:
            records.append({
                "id": str(s.id),
                "apaar_id": s.apaar_id,
                "name": s.get_decrypted_name(),
                "dob": s.get_decrypted_dob().isoformat() if s.get_decrypted_dob() else None,
                "gender": s.gender,
                "institution_id": str(s.institution_id),
                "institution_name": s.institution.name if s.institution else "College",
                "program": s.program,
                "branch": s.branch,
                "verification_status": s.verification_status
            })

        matches = []
        seen_pairs = set()

        # Group records by (DOB, Gender) for efficient high-precision candidate retrieval
        candidate_buckets: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            bucket_key = f"{r['dob']}_{r['gender']}"
            if bucket_key not in candidate_buckets:
                candidate_buckets[bucket_key] = []
            candidate_buckets[bucket_key].append(r)

        for bucket_key, bucket_records in candidate_buckets.items():
            if len(bucket_records) < 2:
                continue

            for i in range(len(bucket_records)):
                for j in range(i + 1, len(bucket_records)):
                    s1 = bucket_records[i]
                    s2 = bucket_records[j]

                    # Only compare across different institutions (cross-institution check)
                    if s1["institution_id"] == s2["institution_id"]:
                        continue

                    pair_key = tuple(sorted([s1["id"], s2["id"]]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    name1 = s1["name"].lower().strip()
                    name2 = s2["name"].lower().strip()

                    token_ratio = fuzz.token_sort_ratio(name1, name2)
                    partial_ratio = fuzz.partial_ratio(name1, name2)
                    name_score = max(token_ratio, partial_ratio)

                    # Compute composite similarity
                    dob_score = 100.0 if s1["dob"] == s2["dob"] else 0.0
                    gender_score = 100.0 if s1["gender"] == s2["gender"] else 0.0

                    composite_score = round(
                        (name_score * 0.6) + (dob_score * 0.3) + (gender_score * 0.1), 1
                    )

                    if composite_score >= similarity_threshold:
                        # Determine severity tier
                        if composite_score >= 95.0:
                            tier = "CRITICAL_DUPLICATE"
                        elif composite_score >= 85.0:
                            tier = "HIGH_CONFIDENCE"
                        else:
                            tier = "POTENTIAL_MATCH"

                        diff_notes = []
                        if name1 != name2:
                            diff_notes.append(f"Name variance: '{s1['name']}' vs '{s2['name']}'")
                        if s1["apaar_id"] == s2["apaar_id"]:
                            diff_notes.append("Identical 12-digit APAAR ID registered across institutions!")
                        else:
                            diff_notes.append(f"Different APAAR IDs: {s1['apaar_id']} vs {s2['apaar_id']}")

                        matches.append({
                            "candidate_id": f"{s1['id'][:8]}_{s2['id'][:8]}",
                            "composite_score": composite_score,
                            "name_similarity": round(name_score, 1),
                            "tier": tier,
                            "explanation": "; ".join(diff_notes),
                            "record_a": s1,
                            "record_b": s2,
                            "detected_at": datetime.now(timezone.utc).isoformat()
                        })

                        if len(matches) >= limit:
                            break
                if len(matches) >= limit:
                    break
            if len(matches) >= limit:
                break

        matches.sort(key=lambda x: x["composite_score"], reverse=True)
        return matches
