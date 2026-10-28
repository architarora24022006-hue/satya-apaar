# SATYA-APAAR (सत्य-अपार) — Master Hackathon Demo Script
### Smart India Hackathon (SIH) 2024 — Problem Statement 26263
**APAAR ID-Based Student Data Management and Verification Platform for AICTE**

---

## 🎯 Executive Pitch (30 Seconds)
> *"Honorable Jury Members, currently across 10,000+ AICTE-approved institutions, student admissions are managed via fragmented CSV uploads with no real-time cross-college cross-referencing. This leads to ghost students claiming scholarship funds, dual-college duplicate admissions, and unregulated over-intake beyond sanctioned limits.*
>
> *We present **SATYA-APAAR (सत्य-अपार)**: India's first end-to-end, zero-trust, DPDP-compliant admission oversight platform powered by Ed25519 cryptographic credentials, Isolation Forest ghost student detection, an autonomous AI Sentinel agent, and an immutable SHA-256 chained audit ledger."*

---

## ⏱️ 5-Minute Demo Flow for Hackathon Judges

### 📌 Minute 1: AICTE Central Command & Safe NL Analytics
- **Navigate to:** `http://localhost:3000/dashboard`
- **What to show:**
  1. **National Heatmap & Real-Time Telemetry:** Point out **44 AICTE Institutions**, **6,535 Students**, and real-time national fill rate.
  2. **Safe Natural Language Analytics Bar:**
     - Type or click: `Top 5 institutions by enrollment`
     - Click **Run**: Watch the system safely map to an allowlisted parameterized query with **0% SQL injection risk**.
     - Highlight the **SQL Translation** transparently displayed to regulators.
  3. **Export Engine:** Click **Excel** or **PDF** in the top action bar to download the live **AICTE Accreditation & Trust Score Audit Report**.
  4. **Hindi / English Toggle:** Click the language switcher in the navbar to demonstrate instant, authentic government Hindi (`सत्य-अपार`).

---

### 📌 Minute 2: Multi-Stage Validation & Ingestion Pipeline
- **Navigate to:** `http://localhost:3000/upload`
- **What to show:**
  1. **Smart Header Auto-Mapping:** Show the header matcher mapping colloquial CSV headers (`Roll No`, `Aadhaar`, `Dept`) to standard AICTE schema.
  2. **Rule Validation Grid:** Filter by rule code:
     - `RULE_FORMAT_CHECKSUM`: Verhoeff checksum algorithm detecting invalid APAAR numbers.
     - `RULE_INTAKE_CAPACITY`: Detecting branch over-admissions.
     - `RULE_CROSS_INSTITUTION_CLASH`: Real-time cross-college clash detection.
  3. **1-Click Auto-Fix & Manual Override:** Click **Auto-Fix** to demonstrate instant flag resolution.

---

### 📌 Minute 3: Planted Anomaly Showcase (The "WOW" Moment)
- **Navigate to:** `http://localhost:3000/intelligence`
- **What to show:**
  1. **Ghost Student Anomaly Radar (Tab 1):**
     - Click on **Balaji College of Engineering (Sonipat)**.
     - Show **Anomaly Score: 92.4/100 (CRITICAL RISK)**.
     - Show Isolation Forest feature explanations:
       - **5.8x surge velocity** in admissions.
       - **84.2% of cohort admitted in final 72 hours**.
       - **62.5% consecutive sequential APAAR IDs** (characteristic of programmatic synthetic student generation).
  2. **Trust Score Leaderboard (Tab 2):**
     - Explain the transparent 4-pillar formula:
       $$\text{Trust Score} = \text{Quality}(30) + \text{Timeliness}(20) + \text{Clearance}(40) + \text{Dispute}(10)$$
     - Show **IIT Delhi (78.2)** vs **Balaji Sonipat (42.1 - Under Sanction Watch)**.
  3. **Predictive Seat Allocation & Real-Time Lock (Tab 4):**
     - Locate **Apex Institute of Technology (Rohtak) — Computer Science Engineering**.
     - Point out **Current Enrolment (124/120)** — 103.3% capacity!
     - Toggle the **Admission Lock Switch** to `LOCKED` — immediately halts further student registrations.

---

### 📌 Minute 4: Zero-Trust Offline Verifier & DPDP Consent Wallet
- **Navigate to:** `http://localhost:3000/verify`
- **What to show:**
  1. **Offline Cryptographic Verifier:**
     - Select demo student **Aarav Sharma (IIT Delhi)**.
     - Show live **Ed25519-signed QR Code**.
     - Click **Verify Offline Credential** — see root authority cryptographic signature verified in **0.1ms without touching the database**.
  2. **Interactive Tamper Simulation:**
     - Click **Simulate Cryptographic Tampering** (changes CGPA/Branch in QR payload).
     - Click **Verify** again — see instant **CRITICAL TAMPER WARNING** in red!
     - Click **Restore Original Payload** to show cryptographic heal.
- **Navigate to:** `http://localhost:3000/consent`
  - Show the **DPDP Act 2023 Granular Consent Matrix** where the student can independently toggle access to PII fields (Aadhaar, DOB, Phone, CGPA).
  - Show simulated **OTP Verification** for elevated background checks.
- **Navigate to:** `http://localhost:3000/audit`
  - Show the unbroken **SHA-256 Chained Audit Trail**.
  - Click **Inject Tampering** into Block #12 — see chain break detected!
  - Click **Auto-Heal Ledger** to restore immutable chain integrity.

---

### 📌 Minute 5: AI Sentinel Autonomous Agent & Human Approval Desk
- **Navigate to:** `http://localhost:3000/sentinel`
- **What to show:**
  1. **Autonomous Triage Workspace:**
     - Select batch **Apex Institute of Technology (Rohtak)**.
     - Click **Run Sentinel Triage**.
     - Watch Sentinel execute its multi-phase autonomous loop:
       - `PLAN` → `INVESTIGATE` → `ACTION` → `COMPLETE`.
     - Inspect the **Typed Tool Executions** drawer (`fetch_upload_batch`, `run_validation`, `forecast_seats`, `request_human_approval`).
  2. **Human Approval Desk:**
     - Switch to tab **Human Approval Desk**.
     - Review the drafted sanction: `Freeze admissions intake for Apex Institute of Technology due to capacity over-enrolment`.
     - Type an officer note and click **Approve & Execute** — branches are instantly locked and chained into the audit ledger!
  3. **Ask Sentinel Copilot:**
     - Switch to **Ask Sentinel** tab.
     - Click: *"Why was Balaji College flagged by the system?"*
     - Watch Sentinel invoke the Isolation Forest diagnostic tool and return detailed statistical findings.

---

## 🔑 Quick Demo Credentials (1-Click Switcher on `/`)

| Role | Email | Password | Scope & Permissions |
|---|---|---|---|
| **AICTE Central Admin** | `admin@aicte.gov.in` | `DemoPass@2026` | National oversight, all analytics, approval authority |
| **Regional Officer** | `ro.north@aicte.gov.in` | `DemoPass@2026` | Northern region inspection, sanction desk approval |
| **Institution Admin** | `admin@iitd.ac.in` | `DemoPass@2026` | Upload batches, manage branch quotas, resolve flags |
| **University Regulator** | `regulator@aktu.ac.in` | `DemoPass@2026` | Affiliated college seat inspection |
| **Employer Verifier** | `verifier@tcs.com` | `DemoPass@2026` | Offline QR verification, selective disclosure |
| **Student** | `aarav.sharma@student.iitd.ac.in` | `DemoPass@2026` | DPDP Consent Wallet, personal QR credential |

---

## ⚡ High-Concurrency Load Testing
To run the Locust load testing benchmark (simulating 10,000+ requests/min):
```bash
cd backend
.\venv\Scripts\python.exe -m locust -f load_test/locustfile.py --headless -u 50 -r 10 --run-time 30s --host http://localhost:8000
```

---

## 🛡️ Architecture & Compliance Badges
- **Cryptographic Standard:** Ed25519 256-bit elliptic curve digital signatures + SHA-256 chained ledger.
- **Privacy Compliance:** Digital Personal Data Protection (DPDP) Act 2023 compliant field-level consent wallet.
- **ML Intelligence:** Scikit-learn Isolation Forest unsupervised anomaly detector + RapidFuzz token sort matching.
- **Agentic Standard:** Claude-compatible Anthropic Tool Use schemas with deterministic fallback & human-in-the-loop approval.
- **Full Test Coverage:** 39 out of 39 automated tests passing across 7 phases.
