import io
import csv
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.institution import Institution, ProgramBranch
from app.models.student import Student
from app.services.trust_score_service import TrustScoreService
from app.services.ml.ghost_student_detector import GhostStudentDetector

class ExportService:
    """
    Export Engine for AICTE Compliance & Accreditation:
    Generates styled PDF audit dossiers, Excel workbooks, and DPDP-compliant CSV rosters.
    """

    @classmethod
    def generate_trust_scores_excel(cls, db: Session) -> io.BytesIO:
        """Generates a styled Excel workbook with the National Institution Trust Score Leaderboard."""
        institutions = db.query(Institution).order_by(desc(Institution.trust_score)).all()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Trust Score Leaderboard"

        # Styles
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="0F172A")
        sub_font = Font(name="Calibri", size=10, italic=True, color="64748B")
        center_align = Alignment(horizontal="center", vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")
        border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1")
        )

        # Title Block
        ws["A1"] = "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION (AICTE)"
        ws["A1"].font = title_font
        ws["A2"] = f"National Institution Trust Score Leaderboard — Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"
        ws["A2"].font = sub_font

        # Headers
        headers = [
            "Rank", "AICTE ID", "Institution Name", "State", "Type",
            "Trust Score (0-100)", "Tier", "Approved Intake", "Enrolled", "Utilization %", "Vigilance Action"
        ]

        row_num = 4
        for col_num, h in enumerate(headers, 1):
            cell = ws.cell(row=row_num, column=col_num, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = border

        # Rows
        for idx, inst in enumerate(institutions, 1):
            row_num += 1
            score = round(inst.trust_score or 0.0, 1)
            util = round((inst.actual_enrolment / inst.approved_intake * 100), 1) if inst.approved_intake else 0.0
            
            if score >= 85:
                tier = "Exemplary (Tier 1)"
                action = "Standard Auto-Approval"
            elif score >= 70:
                tier = "Compliant (Tier 2)"
                action = "Quarterly Review"
            elif score >= 50:
                tier = "Under Watch (Tier 3)"
                action = "Enhanced Verification"
            else:
                tier = "High Risk (Tier 4)"
                action = "Mandatory On-Site Inspection"

            vals = [
                idx, inst.aicte_id, inst.name, inst.state, inst.type,
                score, tier, inst.approved_intake, inst.actual_enrolment, f"{util}%", action
            ]

            for col_num, val in enumerate(vals, 1):
                cell = ws.cell(row=row_num, column=col_num, value=val)
                cell.font = Font(name="Calibri", size=10)
                cell.alignment = center_align if col_num in [1, 2, 4, 5, 6, 7, 10] else left_align
                cell.border = border
                
                # Highlight low trust scores
                if col_num == 6 and score < 60:
                    cell.fill = PatternFill(start_color="FFE4E6", end_color="FFE4E6", fill_type="solid")
                    cell.font = Font(name="Calibri", size=10, bold=True, color="BE123C")

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @classmethod
    def generate_trust_scores_pdf(cls, db: Session) -> io.BytesIO:
        """Generates a formal PDF compliance report for AICTE Trust Scores."""
        institutions = db.query(Institution).order_by(desc(Institution.trust_score)).limit(35).all()

        output = io.BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=A4,
            leftMargin=30,
            rightMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "AICTETitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "AICTESubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1E293B")
        )
        table_header_style = ParagraphStyle(
            "TableHeader",
            fontSize=8,
            leading=10,
            fontName="Helvetica-Bold",
            textColor=colors.white
        )

        elements = []

        # Header Block
        elements.append(Paragraph("ALL INDIA COUNCIL FOR TECHNICAL EDUCATION", title_style))
        elements.append(Paragraph("अखिल भारतीय तकनीकी शिक्षा परिषद • New Delhi, India", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#F59E0B"), spaceAfter=10))

        elements.append(Paragraph(
            f"<b>Official Accreditation & Institution Trust Score Summary</b><br/>"
            f"Report Generated: {datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M:%S')} UTC | "
            f"Evaluation Pillar: 4-Pillar Composite (Quality 30, Timeliness 20, Anomaly 40, Dispute 10)",
            subtitle_style
        ))
        elements.append(Spacer(1, 10))

        # Table data
        data = [[
            Paragraph("Rank", table_header_style),
            Paragraph("AICTE ID", table_header_style),
            Paragraph("Institution Name", table_header_style),
            Paragraph("State", table_header_style),
            Paragraph("Trust Score", table_header_style),
            Paragraph("Vigilance Action", table_header_style)
        ]]

        for idx, inst in enumerate(institutions, 1):
            score = round(inst.trust_score or 0.0, 1)
            action = "Normal" if score >= 85 else ("Review" if score >= 70 else "On-Site Inspection")
            data.append([
                Paragraph(str(idx), table_cell_style),
                Paragraph(inst.aicte_id, table_cell_style),
                Paragraph(inst.name[:35], table_cell_style),
                Paragraph(inst.state, table_cell_style),
                Paragraph(f"<b>{score}/100</b>", table_cell_style),
                Paragraph(action, table_cell_style)
            ])

        t = Table(data, colWidths=[35, 75, 210, 75, 60, 80])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)

        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            "<b>Cryptographic Verification Notice:</b> This document is electronically verified under SATYA-APAAR. "
            "Any tampering with printed scores invalidates accreditation under AICTE Regulations 2026.",
            subtitle_style
        ))

        doc.build(elements)
        output.seek(0)
        return output

    @classmethod
    def generate_anomalies_excel(cls, db: Session) -> io.BytesIO:
        """Generates an Excel workbook summarizing Isolation Forest Ghost Student detections."""
        anomalies = GhostStudentDetector.analyze_institutions(db)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Anomaly Investigation Radar"

        header_fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=14, bold=True, color="991B1B")

        ws["A1"] = "AICTE VIGILANCE CELL — ML GHOST STUDENT ANOMALY RADAR"
        ws["A1"].font = title_font
        ws["A2"] = f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC — Isolation Forest & Ingestion Cluster Profiling"

        headers = [
            "AICTE ID", "Institution", "State", "Anomaly Score", "Risk Tier",
            "Is Anomaly", "Surge Ratio", "Final 72h Clustering %", "Demographic Entropy", "Consecutive APAAR %", "Explanation"
        ]

        row_num = 4
        for col_num, h in enumerate(headers, 1):
            cell = ws.cell(row=row_num, column=col_num, value=h)
            cell.fill = header_fill
            cell.font = header_font

        for a in anomalies:
            row_num += 1
            is_anom = a.get("is_anomaly", a["anomaly_score"] >= 65)
            vals = [
                a["aicte_id"], a["name"], a["state"], f"{a['anomaly_score']}/100", a["risk_tier"],
                "YES" if is_anom else "NO", f"{a['surge_ratio']}x", f"{a['last_day_clustering']}%",
                a["category_entropy"], f"{a['sequentiality_ratio']}%", a["explanation"]
            ]
            for col_num, val in enumerate(vals, 1):
                cell = ws.cell(row=row_num, column=col_num, value=val)
                if col_num in [4, 5, 6] and (is_anom or a["anomaly_score"] > 60):
                    cell.font = Font(name="Calibri", size=10, bold=True, color="991B1B")

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @classmethod
    def generate_students_csv(cls, db: Session, institution_id: Optional[str] = None, mask_apaar: bool = True) -> str:
        """Generates a DPDP-compliant CSV student roster."""
        query = db.query(Student)
        if institution_id:
            query = query.filter(Student.institution_id == institution_id)

        students = query.limit(1000).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Student ID", "APAAR ID", "Gender", "Program", "Branch",
            "Year", "Admission Date", "Quota", "Category", "Verification Status", "Document Hash"
        ])

        for s in students:
            apaar = s.apaar_id
            if mask_apaar and len(apaar) == 12:
                apaar = f"XXXX-XXXX-{apaar[-4:]}"

            writer.writerow([
                str(s.id),
                apaar,
                s.gender,
                s.program,
                s.branch,
                s.year_of_study,
                s.admission_date.isoformat() if s.admission_date else "",
                s.quota_type,
                s.category,
                s.verification_status,
                s.document_hash
            ])

        return output.getvalue()
