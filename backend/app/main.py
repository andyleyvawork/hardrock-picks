import os
from datetime import datetime, timezone, date, timedelta

from fastapi import FastAPI, Query, Header, HTTPException
from sqlalchemy import text

from app.db import engine, DB_INIT_ERROR, DATABASE_URL
from app.bdl import bdl_get
from app.storage import ensure_schema, upsert_teams, upsert_games, read_teams, read_games_between

app = FastAPI(title="Hardrock Picks API")

@app.on_event("startup")
def _startup():
    ensure_schema()

@app.get("/")
def root():
    return {"status": "ok", "service": "backend", "utc": datetime.now(timezone.utc).isoformat()}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/db-check")
def db_check():
    if not DATABASE_URL:
        return {"ok": False, "error": "DATABASE_URL not set"}
    if engine is None:
        return {"ok": False, "error": "DB engine init failed", "details": DB_INIT_ERROR}
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar()
    return {"ok": True, "select_1": value}

# -------------------------
# NBA (BALLDONTLIE) directo
# -------------------------

@app.get("/nba/games")
async def nba_games(days: int = Query(7, ge=1, le=14)):
    today = date.today()
    date_params = [("dates[]", (today + timedelta(days=i)).isoformat()) for i in range(days)]
    return await bdl_get("/nba/v1/games", params=date_params)

@app.get("/nba/teams")
async def nba_teams():
    return await bdl_get("/nba/v1/teams")

@app.get("/nba/players")
async def nba_players(
    search: str = Query(..., min_length=2),
    per_page: int = Query(25, ge=1, le=100),
):
    return await bdl_get("/nba/v1/players", params={"search": search, "per_page": per_page})

# -------------------------
# NBA -> DB (sync + lectura)
# -------------------------

@app.post("/nba/sync/teams")
async def sync_teams():
    payload = await bdl_get("/nba/v1/teams")
    n = upsert_teams(payload)
    return {"ok": True, "upserted": n}

@app.post("/nba/sync/games")
async def sync_games(days: int = Query(7, ge=1, le=14)):
    today = date.today()
    date_params = [("dates[]", (today + timedelta(days=i)).isoformat()) for i in range(days)]
    payload = await bdl_get("/nba/v1/games", params=date_params)
    n = upsert_games(payload)
    return {"ok": True, "upserted": n, "days": days}

@app.get("/nba/db/teams")
def db_teams():
    return {"ok": True, "data": read_teams()}

@app.get("/nba/db/games")
def db_games(days: int = Query(7, ge=1, le=14)):
    start = date.today()
    end = start + timedelta(days=days - 1)
    return {
        "ok": True,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "data": read_games_between(start, end),
    }

# -------------------------
# Cron/Tasks (privado, con token)
# -------------------------

TASK_TOKEN = os.getenv("TASK_TOKEN", "").strip()

def _require_task_token(token: str | None):
    if not TASK_TOKEN:
        raise HTTPException(status_code=500, detail="TASK_TOKEN not set")
    if token != TASK_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/tasks/nba/sync-games")
async def task_sync_games(
    days: int = Query(2, ge=1, le=14),
    x_task_token: str | None = Header(default=None, alias="X-Task-Token"),
):
    """
    Endpoint SOLO para Cron Job (protegido por token).
    Recomendado: days=2 cada 10 min (hoy + mañana) para evitar rate limit.
    """
    _require_task_token(x_task_token)

    today = date.today()
    date_params = [("dates[]", (today + timedelta(days=i)).isoformat()) for i in range(days)]
    payload = await bdl_get("/nba/v1/games", params=date_params)
    n = upsert_games(payload)
    return {"ok": True, "upserted": n, "days": days}
