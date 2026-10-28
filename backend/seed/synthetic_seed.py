import os
import sys
import random
import hashlib
from datetime import datetime, date, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash, encrypt_pii, compute_sha256
from app.models.user import User
from app.models.institution import Institution, ProgramBranch, InstitutionTrustHistory
from app.models.student import Student
from app.models.batch import UploadBatch, ValidationFlag
from app.models.case import Case
from app.models.consent import ConsentWallet
from app.services.apaar_service import ApaarService
from app.services.audit_service import AuditService

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Atharv", "Dhruv", "Kabir", "Rohan", "Ananya", "Diya", "Gauri", "Isha", "Kavya",
    "Meera", "Pooja", "Riya", "Saanvi", "Tanvi", "Zoya", "Sneha", "Priya", "Neha", "Aditi",
    "Vikram", "Rahul", "Amit", "Manish", "Sunil", "Deepak", "Suresh", "Ramesh", "Karthik", "Siddharth",
    "Priyanka", "Shweta", "Deepika", "Kritika", "Preeti", "Sunita", "Lakshmi", "Anjali", "Swati", "Nandini"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Reddy", "Nair", "Iyer", "Rao", "Kumar", "Singh",
    "Mehta", "Joshi", "Bhat", "Deshmukh", "Kulkarni", "Chauhan", "Yadav", "Mishra", "Pandey", "Das",
    "Banerjee", "Chatterjee", "Bose", "Sengupta", "Pillai", "Menon", "Sundaram", "Krishnan", "Agarwal", "Jain",
    "Bansal", "Goel", "Garg", "Malhotra", "Kapoor", "Khanna", "Chopra", "Thakur", "Rathore", "Shekhawat"
]

INDIAN_INSTITUTIONS = [
    # Delhi Region
    {"aicte_id": "1-1000101", "name": "Indian Institute of Technology Delhi", "code": "IITD", "state": "Delhi", "region": "Northern", "type": "Autonomous", "intake": 240},
    {"aicte_id": "1-1000102", "name": "Delhi Technological University", "code": "DTU", "state": "Delhi", "region": "Northern", "type": "Govt", "intake": 200},
    {"aicte_id": "1-1000103", "name": "Netaji Subhas University of Technology", "code": "NSUT", "state": "Delhi", "region": "Northern", "type": "Govt", "intake": 180},
    {"aicte_id": "1-1000104", "name": "Indraprastha Institute of Information Technology", "code": "IIITD", "state": "Delhi", "region": "Northern", "type": "Autonomous", "intake": 160},
    
    # Maharashtra
    {"aicte_id": "1-1000201", "name": "College of Engineering Pune", "code": "COEP", "state": "Maharashtra", "region": "Western", "type": "Govt", "intake": 220},
    {"aicte_id": "1-1000202", "name": "Veermata Jijabai Technological Institute", "code": "VJTI", "state": "Maharashtra", "region": "Western", "type": "Govt", "intake": 180},
    {"aicte_id": "1-1000203", "name": "Sardar Patel Institute of Technology", "code": "SPIT", "state": "Maharashtra", "region": "Western", "type": "Autonomous", "intake": 140},
    {"aicte_id": "1-1000204", "name": "Walchand College of Engineering", "code": "WCE", "state": "Maharashtra", "region": "Western", "type": "Govt", "intake": 150},
    {"aicte_id": "1-1000205", "name": "Visvesvaraya National Institute of Technology", "code": "VNIT", "state": "Maharashtra", "region": "Western", "type": "Autonomous", "intake": 200},
    
    # Karnataka
    {"aicte_id": "1-1000301", "name": "RV College of Engineering", "code": "RVCE", "state": "Karnataka", "region": "Southern", "type": "Autonomous", "intake": 220},
    {"aicte_id": "1-1000302", "name": "BMS College of Engineering", "code": "BMSCE", "state": "Karnataka", "region": "Southern", "type": "Autonomous", "intake": 200},
    {"aicte_id": "1-1000303", "name": "PES University Electronic City Campus", "code": "PESU", "state": "Karnataka", "region": "Southern", "type": "Private", "intake": 180},
    {"aicte_id": "1-1000304", "name": "MS Ramaiah Institute of Technology", "code": "MSRIT", "state": "Karnataka", "region": "Southern", "type": "Autonomous", "intake": 180},
    
    # Tamil Nadu
    {"aicte_id": "1-1000401", "name": "Anna University CEG Campus Chennai", "code": "CEG", "state": "Tamil Nadu", "region": "Southern", "type": "Govt", "intake": 240},
    {"aicte_id": "1-1000402", "name": "PSG College of Technology Coimbatore", "code": "PSG", "state": "Tamil Nadu", "region": "Southern", "type": "Autonomous", "intake": 200},
    {"aicte_id": "1-1000403", "name": "SSN College of Engineering Chennai", "code": "SSN", "state": "Tamil Nadu", "region": "Southern", "type": "Private", "intake": 160},
    {"aicte_id": "1-1000404", "name": "Thiagarajar College of Engineering Madurai", "code": "TCE", "state": "Tamil Nadu", "region": "Southern", "type": "Govt", "intake": 150},
    
    # Uttar Pradesh
    {"aicte_id": "1-1000501", "name": "Dr. A.P.J. Abdul Kalam Technical University Campus", "code": "AKTU", "state": "Uttar Pradesh", "region": "Northern", "type": "Govt", "intake": 250},
    {"aicte_id": "1-1000502", "name": "Harcourt Butler Technical University Kanpur", "code": "HBTU", "state": "Uttar Pradesh", "region": "Northern", "type": "Govt", "intake": 180},
    {"aicte_id": "1-1000503", "name": "Madan Mohan Malaviya University of Tech Gorakhpur", "code": "MMMUT", "state": "Uttar Pradesh", "region": "Northern", "type": "Govt", "intake": 160},
    {"aicte_id": "1-1000504", "name": "JSS Academy of Technical Education Noida", "code": "JSSN", "state": "Uttar Pradesh", "region": "Northern", "type": "Private", "intake": 160},
    {"aicte_id": "1-1000505", "name": "Galgotias College of Engineering and Technology", "code": "GCET", "state": "Uttar Pradesh", "region": "Northern", "type": "Private", "intake": 180},

    # Telangana
    {"aicte_id": "1-1000601", "name": "Jawaharlal Nehru Technological University Hyderabad", "code": "JNTUH", "state": "Telangana", "region": "South-Central", "type": "Govt", "intake": 220},
    {"aicte_id": "1-1000602", "name": "Chaitanya Bharathi Institute of Technology", "code": "CBIT", "state": "Telangana", "region": "South-Central", "type": "Autonomous", "intake": 180},
    {"aicte_id": "1-1000603", "name": "Vasavi College of Engineering Hyderabad", "code": "VCE", "state": "Telangana", "region": "South-Central", "type": "Autonomous", "intake": 160},
    
    # Haryana (Including Over-Intake & Ghost Anomaly test institutions)
    {"aicte_id": "1-1000701", "name": "J.C. Bose UST YMCA Faridabad", "code": "YMCA", "state": "Haryana", "region": "Northern", "type": "Govt", "intake": 180},
    {"aicte_id": "1-1000702", "name": "Deenbandhu Chhotu Ram UST Murthal", "code": "DCRUST", "state": "Haryana", "region": "Northern", "type": "Govt", "intake": 160},
    {"aicte_id": "1-1000703", "name": "The NorthCap University Gurugram", "code": "NCU", "state": "Haryana", "region": "Northern", "type": "Private", "intake": 140},
    # Planted Over-Intake Anomaly:
    {"aicte_id": "1-1000704", "name": "Apex Institute of Advanced Technology Rohtak", "code": "AIAT", "state": "Haryana", "region": "Northern", "type": "Private", "intake": 120, "is_over_intake_target": True},
    # Planted Ghost-Student Anomaly:
    {"aicte_id": "1-1000705", "name": "Shri Balaji Institute of Science and Tech Sonipat", "code": "SBIST", "state": "Haryana", "region": "Northern", "type": "Private", "intake": 120, "is_ghost_target": True},

    # Gujarat
    {"aicte_id": "1-1000801", "name": "L.D. College of Engineering Ahmedabad", "code": "LDCE", "state": "Gujarat", "region": "Western", "type": "Govt", "intake": 220},
    {"aicte_id": "1-1000802", "name": "Institute of Technology Nirma University", "code": "NIRMA", "state": "Gujarat", "region": "Western", "type": "Private", "intake": 180},
    
    # Punjab
    {"aicte_id": "1-1000901", "name": "Punjab Engineering College Chandigarh", "code": "PEC", "state": "Punjab", "region": "Northern", "type": "Govt", "intake": 200},
    {"aicte_id": "1-1000902", "name": "Guru Nanak Dev Engineering College Ludhiana", "code": "GNDEC", "state": "Punjab", "region": "Northern", "type": "Autonomous", "intake": 160},

    # Rajasthan
    {"aicte_id": "1-1001001", "name": "Malaviya National Institute of Technology Jaipur", "code": "MNITJ", "state": "Rajasthan", "region": "Northern", "type": "Autonomous", "intake": 220},
    {"aicte_id": "1-1001002", "name": "MBM Engineering College Jodhpur", "code": "MBM", "state": "Rajasthan", "region": "Northern", "type": "Govt", "intake": 160},

    # West Bengal
    {"aicte_id": "1-1001101", "name": "Jadavpur University Faculty of Engg Kolkata", "code": "JUFE", "state": "West Bengal", "region": "Eastern", "type": "Govt", "intake": 240},
    {"aicte_id": "1-1001102", "name": "Heritage Institute of Technology Kolkata", "code": "HITK", "state": "West Bengal", "region": "Eastern", "type": "Private", "intake": 160},

    # Kerala
    {"aicte_id": "1-1001201", "name": "College of Engineering Trivandrum", "code": "CET", "state": "Kerala", "region": "Southern", "type": "Govt", "intake": 200},
    {"aicte_id": "1-1001202", "name": "TKM College of Engineering Kollam", "code": "TKM", "state": "Kerala", "region": "Southern", "type": "Govt", "intake": 160},

    # Madhya Pradesh
    {"aicte_id": "1-1001301", "name": "Shri Govindram Seksaria ITS Indore", "code": "SGSITS", "state": "Madhya Pradesh", "region": "Central", "type": "Govt", "intake": 180},
    {"aicte_id": "1-1001302", "name": "Jabalpur Engineering College", "code": "JEC", "state": "Madhya Pradesh", "region": "Central", "type": "Govt", "intake": 160},

    # Odisha
    {"aicte_id": "1-1001401", "name": "Odisha University of Technology OUTR Bhubaneswar", "code": "OUTR", "state": "Odisha", "region": "Eastern", "type": "Govt", "intake": 180},
    {"aicte_id": "1-1001402", "name": "Veer Surendra Sai University of Tech Burla", "code": "VSSUT", "state": "Odisha", "region": "Eastern", "type": "Govt", "intake": 180}
]

PROGRAM_BRANCHES = [
    ("UG", "Computer Science & Engineering", 60),
    ("UG", "Electronics & Communication Engineering", 40),
    ("UG", "Mechanical Engineering", 40),
    ("UG", "Artificial Intelligence & Data Science", 30),
    ("PG", "M.Tech in Software Engineering", 18),
    ("PG", "Master of Computer Applications", 30)
]

def seed_database():
    print("🌱 Initializing SATYA-APAAR Synthetic Seed Database...")
    db = SessionLocal()
    try:
        # Recreate tables cleanly
        Base.metadata.create_all(bind=engine)

        # Clear existing data
        db.query(ValidationFlag).delete()
        db.query(Case).delete()
        db.query(ConsentWallet).delete()
        db.query(Student).delete()
        db.query(UploadBatch).delete()
        db.query(ProgramBranch).delete()
        db.query(InstitutionTrustHistory).delete()
        db.query(User).delete()
        db.query(Institution).delete()
        db.commit()

        # 1. Create Institutions
        print(f"🏛️ Seeding {len(INDIAN_INSTITUTIONS)} AICTE-Approved Institutions across India...")
        inst_records = []
        inst_dict = {}

        for inst_data in INDIAN_INSTITUTIONS:
            base_trust = 96.0
            status_val = "ACTIVE"
            if inst_data.get("is_over_intake_target"):
                base_trust = 68.0
                status_val = "WARNING"
            elif inst_data.get("is_ghost_target"):
                base_trust = 72.0
                status_val = "WARNING"

            inst = Institution(
                aicte_id=inst_data["aicte_id"],
                name=inst_data["name"],
                code=inst_data["code"],
                state=inst_data["state"],
                region=inst_data["region"],
                type=inst_data["type"],
                trust_score=base_trust,
                approved_intake=inst_data["intake"],
                actual_enrolment=0,  # Will increment as students are added
                supernumerary_intake=int(inst_data["intake"] * 0.15),
                status=status_val,
                contact_email=f"registrar@{inst_data['code'].lower()}.edu.in",
                phone=f"+91-{random.randint(7000000000, 9999999999)}",
                address=f"Campus Road, Sector {random.randint(1, 40)}, {inst_data['state']}, India"
            )
            db.add(inst)
            inst_records.append(inst)

        db.commit()

        # Re-fetch institutions with IDs
        for inst in db.query(Institution).all():
            inst_dict[inst.code] = inst
            # Add academic branches
            for prog, branch, intake in PROGRAM_BRANCHES:
                pb = ProgramBranch(
                    institution_id=str(inst.id),
                    program=prog,
                    branch=branch,
                    academic_year="2025-2026",
                    approved_intake=intake,
                    enrolled_count=0,
                    supernumerary_intake=int(intake * 0.15)
                )
                db.add(pb)
            
            # Add Trust History
            th = InstitutionTrustHistory(
                institution_id=str(inst.id),
                score=inst.trust_score,
                data_quality_factor=0.98,
                timeliness_factor=0.95,
                anomaly_penalty=5.0 if inst.trust_score < 80 else 0.0,
                resolution_speed_factor=0.92
            )
            db.add(th)

        db.commit()

        # 2. Create Users for all 6 RBAC roles
        print("👤 Seeding RBAC Users across all 6 roles...")
        default_pwd_hash = get_password_hash("Password@123")
        
        users_data = [
            # AICTE Central Admin
            {
                "email": "admin@aicte.gov.in",
                "full_name": "Dr. Anil Sahasrabudhe",
                "role": "AICTE_ADMIN",
                "institution_id": None,
                "mfa_enabled": False
            },
            # Regional Officer
            {
                "email": "ro.delhi@aicte.gov.in",
                "full_name": "Shri Rajesh Verma (RO Delhi)",
                "role": "REGIONAL_OFFICER",
                "institution_id": None,
                "mfa_enabled": False
            },
            # Institution Admin 1: IIT Delhi
            {
                "email": "admin@iitd.ac.in",
                "full_name": "Prof. S. Ranganathan (IITD Admin)",
                "role": "INSTITUTION_ADMIN",
                "institution_id": str(inst_dict["IITD"].id),
                "mfa_enabled": False
            },
            # Institution Admin 2: AKTU Lucknow
            {
                "email": "admin@aktu.ac.in",
                "full_name": "Dr. P.K. Mishra (AKTU Admin)",
                "role": "INSTITUTION_ADMIN",
                "institution_id": str(inst_dict["AKTU"].id),
                "mfa_enabled": False
            },
            # Institution Admin 3: Apex Rohtak (Over-intake)
            {
                "email": "admin@aiat.edu.in",
                "full_name": "Shri Mukesh Dalal (AIAT Admin)",
                "role": "INSTITUTION_ADMIN",
                "institution_id": str(inst_dict["AIAT"].id),
                "mfa_enabled": False
            },
            # University / Regulator
            {
                "email": "regulator@aktu.ac.in",
                "full_name": "Controller of Examinations (State Univ)",
                "role": "UNIVERSITY_REGULATOR",
                "institution_id": None,
                "mfa_enabled": False
            },
            # Employer Verifier
            {
                "email": "tcs.verifier@tcs.com",
                "full_name": "Meenakshi Sundaram (TCS Global BG)",
                "role": "EMPLOYER_VERIFIER",
                "institution_id": None,
                "mfa_enabled": False
            },
            # Student User
            {
                "email": "aarav.sharma@satya.gov.in",
                "full_name": "Aarav Sharma",
                "role": "STUDENT",
                "institution_id": str(inst_dict["IITD"].id),
                "mfa_enabled": True
            }
        ]

        for u_data in users_data:
            user = User(
                email=u_data["email"],
                hashed_password=default_pwd_hash,
                full_name=u_data["full_name"],
                role=u_data["role"],
                institution_id=u_data["institution_id"],
                is_active=True,
                mfa_enabled=u_data["mfa_enabled"],
                mfa_secret="SATYA_DEMO_SECRET"
            )
            db.add(user)
        db.commit()

        # 3. Seed Students (Target: ~5,000 students across 40 colleges)
        print("🎓 Generating 5,000 synthetic student records with AES-256 encryption...")
        random.seed(42)  # Deterministic seed for reproducible testing

        student_counter = 10000000000  # 11 digits base for APAAR generator
        total_students_created = 0
        all_students = []

        # Target 5,000 total students: average ~125 students per college
        colleges = list(inst_dict.values())
        
        for inst in colleges:
            # Over-intake college gets 138 students (intake is 120 -> 115% breach)
            if inst.code == "AIAT":
                num_students = 138
            # Ghost anomaly college gets 120 students with tight clustering
            elif inst.code == "SBIST":
                num_students = 120
            else:
                num_students = int(inst.approved_intake * random.uniform(0.70, 0.95))
            
            # Select branch distribution
            branches = db.query(ProgramBranch).filter(ProgramBranch.institution_id == str(inst.id)).all()
            
            for i in range(num_students):
                student_counter += 1
                base_11_digits = str(student_counter).zfill(11)
                valid_apaar = ApaarService.generate_valid_apaar(base_11_digits)
                
                f_name = random.choice(FIRST_NAMES)
                l_name = random.choice(LAST_NAMES)
                full_name = f"{f_name} {l_name}"
                
                # Realistic DOB: 18-23 years old
                birth_year = random.randint(2002, 2007)
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)
                dob_val = date(birth_year, birth_month, birth_day)
                
                # Admission date in 2025 academic season
                if inst.code == "SBIST":
                    # Ghost anomaly: 85% admissions on the exact final 2 days (Aug 30-31, 2025)
                    adm_date = date(2025, 8, 30) if random.random() < 0.85 else date(2025, 8, 15)
                else:
                    adm_day = random.randint(1, 30)
                    adm_date = date(2025, 7, adm_day) if random.random() < 0.6 else date(2025, 8, adm_day)

                # Quota & Categories
                cat_rand = random.random()
                if cat_rand < 0.45:
                    category = "General"
                elif cat_rand < 0.72:
                    category = "OBC"
                elif cat_rand < 0.87:
                    category = "SC"
                elif cat_rand < 0.94:
                    category = "ST"
                else:
                    category = "EWS"

                quota_rand = random.random()
                if quota_rand < 0.80:
                    quota = "Merit"
                elif quota_rand < 0.92:
                    quota = "Management"
                elif quota_rand < 0.96:
                    quota = "NRI"
                else:
                    quota = "Supernumerary"

                chosen_pb = random.choice(branches)
                doc_hash = hashlib.sha256(f"{valid_apaar}_{full_name}_{dob_val}".encode("utf-8")).hexdigest()

                student = Student(
                    apaar_id=valid_apaar,
                    institution_id=str(inst.id),
                    program_branch_id=str(chosen_pb.id),
                    name_encrypted=encrypt_pii(full_name),
                    dob_encrypted=encrypt_pii(dob_val.isoformat()),
                    cached_name=full_name,
                    cached_dob=dob_val,
                    gender="Male" if random.random() < 0.55 else "Female",
                    program=chosen_pb.program,
                    branch=chosen_pb.branch,
                    year_of_study=1,
                    admission_date=adm_date,
                    quota_type=quota,
                    category=category,
                    is_supernumerary=(quota == "Supernumerary"),
                    is_nri=(quota == "NRI"),
                    is_oci=False,
                    is_foreign_national=False,
                    document_hash=doc_hash,
                    verification_status="VALIDATED"
                )
                db.add(student)
                all_students.append(student)
                total_students_created += 1

                if total_students_created % 500 == 0:
                    db.commit()
                    print(f"   ...seeded {total_students_created} students")

        db.commit()
        print(f"✅ Generated {total_students_created} valid student records.")

        # 4. Plant Deliberate Errors & Fraud Patterns for Demo Script
        print("⚠️ Planting deliberate fraud patterns & validation anomalies for hackathon demonstration...")

        # A. Planted Cross-College Clash #1: Rohan Verma active at IITD and AKTU
        clash_apaar_1 = "992817263541"
        clash_student_1_iitd = Student(
            apaar_id=clash_apaar_1,
            institution_id=str(inst_dict["IITD"].id),
            name_encrypted=encrypt_pii("Rohan Verma"),
            dob_encrypted=encrypt_pii("2004-05-14"),
            cached_name="Rohan Verma",
            cached_dob=date(2004, 5, 14),
            gender="Male",
            program="UG",
            branch="Computer Science & Engineering",
            year_of_study=1,
            admission_date=date(2025, 7, 10),
            quota_type="Merit",
            category="General",
            document_hash=hashlib.sha256(b"clash_doc_1").hexdigest(),
            verification_status="FLAGGED"
        )
        db.add(clash_student_1_iitd)

        clash_student_1_aktu = Student(
            apaar_id=clash_apaar_1,
            institution_id=str(inst_dict["AKTU"].id),
            name_encrypted=encrypt_pii("Rohan Verma"),
            dob_encrypted=encrypt_pii("2004-05-14"),
            cached_name="Rohan Verma",
            cached_dob=date(2004, 5, 14),
            gender="Male",
            program="UG",
            branch="Information Technology",
            year_of_study=1,
            admission_date=date(2025, 8, 2),
            quota_type="Management",
            category="General",
            document_hash=hashlib.sha256(b"clash_doc_1_aktu").hexdigest(),
            verification_status="FLAGGED"
        )
        db.add(clash_student_1_aktu)

        # Flag and Case for Clash #1
        flag_clash_1 = ValidationFlag(
            apaar_id=clash_apaar_1,
            institution_id=str(inst_dict["AKTU"].id),
            rule_code="CROSS_INSTITUTION_DUPLICATE",
            severity="CRITICAL",
            description="Active concurrent enrolment detected across multiple AICTE institutions: IIT Delhi and AKTU Lucknow.",
            fix_suggestion="Issue dual-enrolment show-cause notice and verify bona fide admission letter."
        )
        db.add(flag_clash_1)

        case_clash_1 = Case(
            case_number="CASE-2026-0001",
            title="Cross-College Dual Enrolment Clash: Rohan Verma",
            institution_id=str(inst_dict["IITD"].id),
            clash_institution_id=str(inst_dict["AKTU"].id),
            related_student_apaar=clash_apaar_1,
            status="OPEN",
            priority="URGENT",
            sla_deadline=datetime.now(timezone.utc) + timedelta(hours=48),
            opened_by_type="SENTINEL",
            description="Student APAAR 992817263541 submitted by AKTU Lucknow is already registered as an active full-time student at IIT Delhi.",
            action_draft="Formal inquiry notice drafted for both registrars regarding dual seat blockage."
        )
        db.add(case_clash_1)

        # B. Planted Cross-College Clash #2: Pooja Sundaram active at CEG Chennai and RVCE Bengaluru
        clash_apaar_2 = "883719204852"
        clash_student_2_ceg = Student(
            apaar_id=clash_apaar_2,
            institution_id=str(inst_dict["CEG"].id),
            name_encrypted=encrypt_pii("Pooja Sundaram"),
            dob_encrypted=encrypt_pii("2003-11-20"),
            cached_name="Pooja Sundaram",
            cached_dob=date(2003, 11, 20),
            gender="Female",
            program="UG",
            branch="Electronics & Communication Engineering",
            year_of_study=1,
            admission_date=date(2025, 7, 18),
            quota_type="Merit",
            category="OBC",
            document_hash=hashlib.sha256(b"clash_doc_2_ceg").hexdigest(),
            verification_status="FLAGGED"
        )
        db.add(clash_student_2_ceg)

        flag_clash_2 = ValidationFlag(
            apaar_id=clash_apaar_2,
            institution_id=str(inst_dict["RVCE"].id),
            rule_code="CROSS_INSTITUTION_DUPLICATE",
            severity="CRITICAL",
            description="Active concurrent enrolment clash detected: CEG Chennai and RV College of Engineering Bengaluru.",
            fix_suggestion="Confirm TC (Transfer Certificate) and migration status."
        )
        db.add(flag_clash_2)

        # C. Planted 4 Invalid APAAR ID Records
        invalid_apaar_samples = [
            ("1234567890", "FORMAT_LENGTH_INVALID", "APAAR ID has only 10 digits instead of 12 digits."),
            ("9876543210123", "FORMAT_LENGTH_INVALID", "APAAR ID exceeds length (13 digits)."),
            ("112233445567", "CHECKSUM_VERHOEFF_FAILED", "Failed Verhoeff checksum algorithm check."),
            ("998877665541", "CHECKSUM_VERHOEFF_FAILED", "Failed Verhoeff checksum algorithm check.")
        ]
        for inv_id, rule, desc in invalid_apaar_samples:
            inv_student = Student(
                apaar_id=inv_id,
                institution_id=str(inst_dict["GCET"].id),
                name_encrypted=encrypt_pii("Sample Invalid Record"),
                dob_encrypted=encrypt_pii("2004-01-01"),
                cached_name="Sample Invalid Record",
                cached_dob=date(2004, 1, 1),
                gender="Male",
                program="UG",
                branch="Mechanical Engineering",
                year_of_study=1,
                admission_date=date(2025, 8, 10),
                quota_type="Merit",
                category="General",
                document_hash=hashlib.sha256(inv_id.encode()).hexdigest(),
                verification_status="FLAGGED"
            )
            db.add(inv_student)
            
            flag_inv = ValidationFlag(
                apaar_id=inv_id,
                institution_id=str(inst_dict["GCET"].id),
                rule_code=rule,
                severity="HIGH",
                description=desc,
                fix_suggestion="Re-verify APAAR ID from candidate's ABC ID or DigiLocker card."
            )
            db.add(flag_inv)

        # D. Planted Over-Intake Flag for Apex Institute Rohtak
        flag_over_intake = ValidationFlag(
            apaar_id=None,
            institution_id=str(inst_dict["AIAT"].id),
            rule_code="APPROVED_INTAKE_EXCEEDED",
            severity="CRITICAL",
            description="Actual admissions (138) exceed sanctioned AICTE approved intake (120) by 15.0%.",
            fix_suggestion="Freeze further admissions. Require supernumerary justification and executive approval."
        )
        db.add(flag_over_intake)

        case_over_intake = Case(
            case_number="CASE-2026-0002",
            title="Sanctioned Intake Breach: Apex Institute of Advanced Technology",
            institution_id=str(inst_dict["AIAT"].id),
            status="PENDING_APPROVAL",
            priority="HIGH",
            sla_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
            opened_by_type="SENTINEL",
            description="Institution enrolled 138 students against 120 sanctioned seats without prior supernumerary sanction.",
            action_draft="Initiate AICTE Section 10(k) seat lock and issue show-cause penalty."
        )
        db.add(case_over_intake)

        # Update institution actual enrolment counts
        for inst in db.query(Institution).all():
            count = db.query(Student).filter(Student.institution_id == str(inst.id)).count()
            inst.actual_enrolment = count
        db.commit()

        # 5. Create Student Consent Wallet for Demo Student (Aarav Sharma)
        print("🔐 Initializing Student Consent Wallet & Selective Disclosure proofs...")
        consent = ConsentWallet(
            student_apaar_id=all_students[0].apaar_id,
            verifier_type="EMPLOYER",
            allowed_fields=["apaar_id", "name", "program", "branch", "year_of_study", "institution_name"],
            is_active=True,
            otp_code="782910",
            expires_at=datetime.now(timezone.utc) + timedelta(days=90)
        )
        db.add(consent)
        db.commit()

        # 6. Initialize SHA-256 Hash-Chained Audit Trail
        print("⛓️ Generating Genesis block and initial cryptographic audit chain...")
        # Genesis block
        AuditService.append_log(
            db=db,
            action="SYSTEM_GENESIS_INITIALIZATION",
            entity_type="SYSTEM",
            entity_id="AICTE_CENTRAL_CORE",
            role="AICTE_ADMIN",
            user_id="SYSTEM_ROOT",
            user_email="system@aicte.gov.in",
            details={"version": "1.0.0", "message": "SATYA-APAAR Ledger Genesis Block Established"}
        )

        # Seed institution onboarding logs
        for inst in INDIAN_INSTITUTIONS[:5]:
            AuditService.append_log(
                db=db,
                action="INSTITUTION_REGISTERED",
                entity_type="INSTITUTION",
                entity_id=inst["aicte_id"],
                role="AICTE_ADMIN",
                user_id="SYSTEM_ROOT",
                user_email="admin@aicte.gov.in",
                details={"name": inst["name"], "intake": inst["intake"], "state": inst["state"]}
            )

        # Seed batch upload log
        AuditService.append_log(
            db=db,
            action="BULK_STUDENT_BATCH_INGESTED",
            entity_type="UPLOAD_BATCH",
            entity_id="BATCH-2026-SEED-01",
            role="INSTITUTION_ADMIN",
            user_id="SYSTEM_ROOT",
            user_email="admin@iitd.ac.in",
            details={"total_records": 5000, "flagged": 8, "status": "COMPLETED"}
        )

        # Check chain integrity
        integrity = AuditService.verify_chain_integrity(db)
        print(f"🔒 Cryptographic Audit Chain Status: {integrity['message']}")

        print("\n✨ SATYA-APAAR Synthetic Database Seed Completed Successfully!")
        print(f"   - Total Institutions: {len(INDIAN_INSTITUTIONS)}")
        print(f"   - Total Students: {db.query(Student).count()}")
        print(f"   - Planted Validation Flags: {db.query(ValidationFlag).count()}")
        print(f"   - Planted Resolution Cases: {db.query(Case).count()}")
        print(f"   - Audit Chain Blocks: {db.query(AuditService).count() if hasattr(AuditService, 'count') else 'Chain verified'}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
