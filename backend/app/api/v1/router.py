from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.institutions import router as institutions_router
from app.api.v1.students import router as students_router
from app.api.v1.upload import router as upload_router
from app.api.v1.cases import router as cases_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.realtime import router as realtime_router
from app.api.v1.audit import router as audit_router
from app.api.v1.health import router as health_router
from app.api.v1.verification import router as verification_router
from app.api.v1.consent import router as consent_router
from app.api.v1.ml import router as ml_router
from app.api.v1.sentinel import router as sentinel_router
from app.api.v1.export import router as export_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(institutions_router)
api_router.include_router(students_router)
api_router.include_router(upload_router)
api_router.include_router(cases_router)
api_router.include_router(analytics_router)
api_router.include_router(realtime_router)
api_router.include_router(audit_router)
api_router.include_router(health_router)
api_router.include_router(verification_router)
api_router.include_router(consent_router)
api_router.include_router(ml_router)
api_router.include_router(sentinel_router)
api_router.include_router(export_router)



