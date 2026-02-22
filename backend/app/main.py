from fastapi import FastAPI, Query
from datetime import datetime, timezone, date, timedelta
from sqlalchemy import text

from app.db import engine, DB_INIT_ERROR, DATABASE_URL
from app.bdl import bdl_get

app = FastAPI(title="Hardrock Picks API")

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
# NBA (BALLDONTLIE)
# -------------------------

@app.get("/nba/games")
async def nba_games(days: int = Query(7, ge=1, le=14)):
    """
    Devuelve juegos desde hoy y los próximos `days` días (incluye hoy).
    Ej: days=7 => hoy + 6 días más
    """
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
    # search param: ?search=davis (documentado por BALLDONTLIE)
    return await bdl_get("/nba/v1/players", params={"search": search, "per_page": per_page})
