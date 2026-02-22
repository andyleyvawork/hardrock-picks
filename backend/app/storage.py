from datetime import date
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db import engine
from app.models import metadata, nba_teams, nba_games

def ensure_schema():
    if engine is None:
        return
    metadata.create_all(engine)

def upsert_teams(payload: dict) -> int:
    """
    payload = respuesta completa de /nba/v1/teams
    """
    if engine is None:
        return 0

    teams = payload.get("data", []) or []
    if not teams:
        return 0

    rows = []
    for t in teams:
        rows.append({
            "id": t.get("id"),
            "abbreviation": t.get("abbreviation"),
            "city": t.get("city"),
            "conference": t.get("conference"),
            "division": t.get("division"),
            "name": t.get("name"),
            "full_name": t.get("full_name"),
            "raw": t,
        })

    stmt = insert(nba_teams).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[nba_teams.c.id],
        set_={
            "abbreviation": stmt.excluded.abbreviation,
            "city": stmt.excluded.city,
            "conference": stmt.excluded.conference,
            "division": stmt.excluded.division,
            "name": stmt.excluded.name,
            "full_name": stmt.excluded.full_name,
            "raw": stmt.excluded.raw,
        }
    )

    with engine.begin() as conn:
        conn.execute(stmt)

    return len(rows)

def _parse_game_day(game: dict) -> date | None:
    """
    balldontlie suele traer "date" en ISO.
    Convertimos a date sin depender de librerías extra.
    """
    s = (game.get("date") or "").strip()
    if not s:
        return None
    # maneja "Z"
    s = s.replace("Z", "+00:00")
    try:
        # YYYY-MM-DDTHH:MM:SS...
        return date.fromisoformat(s[:10])
    except Exception:
        return None

def upsert_games(payload: dict) -> int:
    """
    payload = respuesta completa de /nba/v1/games
    """
    if engine is None:
        return 0

    games = payload.get("data", []) or []
    if not games:
        return 0

    rows = []
    for g in games:
        home = g.get("home_team") or {}
        vis = g.get("visitor_team") or {}

        rows.append({
            "id": g.get("id"),
            "game_day": _parse_game_day(g),
            "season": g.get("season"),
            "status": g.get("status"),
            "postseason": g.get("postseason"),
            "home_team_id": home.get("id"),
            "visitor_team_id": vis.get("id"),
            "home_team_score": g.get("home_team_score"),
            "visitor_team_score": g.get("visitor_team_score"),
            "raw": g,
        })

    stmt = insert(nba_games).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[nba_games.c.id],
        set_={
            "game_day": stmt.excluded.game_day,
            "season": stmt.excluded.season,
            "status": stmt.excluded.status,
            "postseason": stmt.excluded.postseason,
            "home_team_id": stmt.excluded.home_team_id,
            "visitor_team_id": stmt.excluded.visitor_team_id,
            "home_team_score": stmt.excluded.home_team_score,
            "visitor_team_score": stmt.excluded.visitor_team_score,
            "raw": stmt.excluded.raw,
        }
    )

    with engine.begin() as conn:
        conn.execute(stmt)

    return len(rows)

def read_teams():
    if engine is None:
        return []
    with engine.connect() as conn:
        rows = conn.execute(select(nba_teams)).mappings().all()
    return [dict(r) for r in rows]

def read_games_between(start_day: date, end_day: date):
    """
    end_day inclusive
    """
    if engine is None:
        return []
    q = (
        select(nba_games)
        .where(nba_games.c.game_day >= start_day)
        .where(nba_games.c.game_day <= end_day)
        .order_by(nba_games.c.game_day.asc(), nba_games.c.id.asc())
    )
    with engine.connect() as conn:
        rows = conn.execute(q).mappings().all()
    return [dict(r) for r in rows]
