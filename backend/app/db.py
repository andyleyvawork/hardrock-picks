import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

engine = None
SessionLocal = None

if DATABASE_URL:
    engine = create_engine(_normalize_db_url(DATABASE_URL), pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
