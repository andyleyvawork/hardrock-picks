from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, Boolean,
    Date, JSON
)

metadata = MetaData()

nba_teams = Table(
    "nba_teams",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("abbreviation", String(8)),
    Column("city", String(64)),
    Column("conference", String(16)),
    Column("division", String(32)),
    Column("name", String(64)),
    Column("full_name", String(128)),
    Column("raw", JSON, nullable=False),
)

nba_games = Table(
    "nba_games",
    metadata,
    Column("id", Integer, primary_key=True),              # game id de balldontlie
    Column("game_day", Date, index=True),                 # para filtrar fácil por día
    Column("season", Integer),
    Column("status", String(64)),
    Column("postseason", Boolean),
    Column("home_team_id", Integer),
    Column("visitor_team_id", Integer),
    Column("home_team_score", Integer),
    Column("visitor_team_score", Integer),
    Column("raw", JSON, nullable=False),
)
