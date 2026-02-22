from fastapi import FastAPI
from datetime import datetime, timezone

app = FastAPI(title="Hardrock Picks API")

@app.get("/")
def root():
    return {"status": "ok", "service": "backend", "utc": datetime.now(timezone.utc).isoformat()}

@app.get("/health")
def health():
    return {"ok": True}
