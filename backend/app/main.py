import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("satya-apaar")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    try:
        logger.info("Initializing database schema...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")

        # Auto-seed on first deployment if empty
        from app.core.database import SessionLocal
        from app.models.user import User
        with SessionLocal() as db:
            if db.query(User).count() == 0:
                logger.info("Database is empty. Populating with synthetic SIH seed data...")
                try:
                    from seed.synthetic_seed import seed_database
                    seed_database()
                    logger.info("Database auto-seeded successfully.")
                except Exception as se:
                    logger.warning(f"Auto-seeding encountered non-fatal notice: {se}")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    yield
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SATYA-APAAR: AICTE APAAR ID-Based Student Data Management and Verification Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open in development for Next.js and external callers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "description": "AICTE APAAR ID-based Student Data Management and Verification Platform",
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
