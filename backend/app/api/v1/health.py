from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_public_key_b64

router = APIRouter(prefix="/health", tags=["Health & System Diagnostics"])

@router.get("/")
def get_system_health(db: Session = Depends(get_db)):
    """System liveness and diagnostics endpoint."""
    db_status = "HEALTHY"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"UNHEALTHY: {str(e)}"

    pub_key = get_public_key_b64()

    return {
        "status": "ONLINE",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "ed25519_public_key": pub_key,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
