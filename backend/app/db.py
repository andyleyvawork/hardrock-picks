import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

log = logging.getLogger("db")

def _normalize_db_url(url: str) -> str:
    # Render a veces usa postgres:// y SQLAlchemy prefiere postgresql://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

engine = None
SessionLocal = None
DB_INIT_ERROR = None

if DATABASE_URL:
    try:
        engine = create_engine(_normalize_db_url(DATABASE_URL), pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        # Importante: NO tumbamos el servidor, solo guardamos el error
        DB_INIT_ERROR = f"{type(e).__name__}: {e}"
        log.exception("DB engine init failed")
        engine = None
        SessionLocal = None
