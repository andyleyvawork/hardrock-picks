from fastapi import FastAPI
from datetime import datetime, timezone
from sqlalchemy import text

from app.db import engine, DB_INIT_ERROR, DATABASE_URL

app = FastAPI(title="Hardrock Picks API")

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "backend",
        "utc": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/db-check")
def db_check():
    if not DATABASE_URL:
        return {"ok": False, "error": "DATABASE_URL not set"}

    if engine is None:
        return {
            "ok": False,
            "error": "DB engine init failed",
            "details": DB_INIT_ERROR
        }

    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar()
    return {"ok": True, "select_1": value}
