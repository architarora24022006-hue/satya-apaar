import json
import random
from locust import HttpUser, task, between, events

class SatyaApaarLoadTester(HttpUser):
    """
    Locust Load Test Suite for SATYA-APAAR.
    Simulates high-concurrency traffic targeting 10,000+ operations/min:
    - DPDP Verification requests
    - Offline cryptographic Ed25519 signature checks
    - Student consent wallet queries
    - National real-time analytics
    - Safe Natural Language analytics bar queries
    - Sentinel AI Chat queries
    """
    wait_time = between(0.1, 0.5)  # Fast turnaround for stress testing

    sample_apaars = [
        "234567890123",  # High-trust student
        "998877665544",  # Flagged student
        "345678901234",  # Standard student
        "456789012345",  # Student
        "567890123456",  # Student
    ]

    nl_queries = [
        "top 5 institutions by enrollment",
        "colleges with trust score below 70",
        "gender distribution across students",
        "state wise student summary",
        "branches near full seat capacity",
        "ghost student anomaly overview"
    ]

    @task(10)
    def test_health_liveness(self):
        """High-frequency load balancer liveness probe."""
        self.client.get("/api/v1/health/live", name="/health/live")

    @task(15)
    def test_national_dashboard_analytics(self):
        """Regulators inspecting AICTE Central Command heatmap and charts."""
        headers = {"Authorization": "Bearer mock-token-for-benchmarking"}
        self.client.get("/api/v1/analytics/national", headers=headers, name="/analytics/national")

    @task(25)
    def test_dpdp_student_verification(self):
        """Employers and universities verifying student credentials."""
        apaar = random.choice(self.sample_apaars)
        payload = {
            "apaar_id": apaar,
            "requested_fields": ["name", "program", "branch", "year_of_study"],
            "verifier_name": "TCS Recruitment Cell",
            "verifier_org": "Tata Consultancy Services",
            "verifier_role": "EMPLOYER_VERIFIER",
            "purpose": "Campus Recruitment Drive 2026"
        }
        self.client.post("/api/v1/verification/verify", json=payload, name="/verification/verify")

    @task(10)
    def test_offline_cryptographic_verification(self):
        """Zero-trust offline verifier checking QR code payload."""
        payload = {
            "payload_data": {
                "apaar_id": "234567890123",
                "name": "Aarav Sharma",
                "institution": "IIT Delhi",
                "program": "B.Tech",
                "branch": "Computer Science & Engineering",
                "year": 4,
                "issued_at": "2026-10-27T12:00:00Z"
            },
            "signature_b64": "fakesig_for_load_simulation_test_signature",
            "public_key_b64": None
        }
        self.client.post("/api/v1/verification/verify-offline", json=payload, name="/verification/verify-offline")

    @task(15)
    def test_consent_wallet_fetch(self):
        """Students reviewing their DPDP field permissions."""
        apaar = random.choice(self.sample_apaars)
        self.client.get(f"/api/v1/consent/wallet/{apaar}", name="/consent/wallet/[apaar]")

    @task(10)
    def test_safe_nl_analytics(self):
        """Regulators querying natural language analytics bar."""
        q = random.choice(self.nl_queries)
        self.client.post("/api/v1/analytics/nl-query", json={"query": q}, name="/analytics/nl-query")

    @task(5)
    def test_sentinel_copilot_chat(self):
        """Officers consulting AI Sentinel agent."""
        self.client.post(
            "/api/v1/sentinel/chat",
            json={"message": "Why was Balaji College flagged?"},
            name="/sentinel/chat"
        )
