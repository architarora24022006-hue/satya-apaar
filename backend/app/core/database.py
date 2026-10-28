import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    try:
        if db_url.startswith("postgresql"):
            # Test engine connectivity
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                connect_args={"connect_timeout": 3}
            )
            with engine.connect():
                logger.info(f"Connected to PostgreSQL database at {db_url.split('@')[-1] if '@' in db_url else db_url}")
                return engine
    except Exception as e:
        if settings.SQLITE_FALLBACK:
            logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite: {settings.SQLITE_URL}")
            return create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False}
            )
        raise e

    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )

    return create_engine(db_url)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
