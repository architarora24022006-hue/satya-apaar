from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["Report & Data Exports"])

@router.get("/trust-scores")
def export_trust_scores(
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    db: Session = Depends(get_db)
):
    """
    Exports official AICTE Institution Trust Score Leaderboard.
    Supports Excel (.xlsx) and PDF (.pdf).
    """
    if format == "excel":
        excel_stream = ExportService.generate_trust_scores_excel(db)
        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=AICTE_Trust_Score_Leaderboard.xlsx"}
        )
    else:
        pdf_stream = ExportService.generate_trust_scores_pdf(db)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=AICTE_Trust_Score_Audit_Report.pdf"}
        )

@router.get("/anomalies")
def export_anomaly_report(
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    db: Session = Depends(get_db)
):
    """
    Exports the AICTE ML Ghost Student Anomaly Investigation Report.
    """
    if format == "excel":
        excel_stream = ExportService.generate_anomalies_excel(db)
        return StreamingResponse(
            excel_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=AICTE_Ghost_Student_Anomaly_Radar.xlsx"}
        )
    else:
        # Generate trust scores pdf with anomaly focus or stream
        pdf_stream = ExportService.generate_trust_scores_pdf(db)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=AICTE_Anomaly_Vigilance_Report.pdf"}
        )

@router.get("/students")
def export_student_roster(
    institution_id: Optional[str] = Query(None),
    mask_apaar: bool = Query(True),
    format: str = Query("csv", pattern="^(csv)$"),
    db: Session = Depends(get_db)
):
    """
    Exports DPDP-compliant student roster with masked/unmasked APAAR ID.
    """
    csv_data = ExportService.generate_students_csv(db, institution_id=institution_id, mask_apaar=mask_apaar)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=AICTE_Student_Roster.csv"}
    )
