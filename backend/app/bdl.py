import os
import httpx
from fastapi import HTTPException

BDL_BASE_URL = os.getenv("BDL_BASE_URL", "https://api.balldontlie.io").rstrip("/")
BDL_API_KEY = (os.getenv("BALLDONTLIE_API_KEY") or os.getenv("BDL_API_KEY") or "").strip()

def _headers():
    if not BDL_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Falta BALLDONTLIE_API_KEY en Render (Environment Variables).",
        )
    # BALLDONTLIE usa header Authorization: API_KEY
    return {"Authorization": BDL_API_KEY}

async def bdl_get(path: str, params=None):
    url = f"{BDL_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, headers=_headers(), params=params)

    if r.status_code >= 400:
        # Intentamos dar el error en JSON si viene así
        try:
            payload = r.json()
        except Exception:
            payload = {"error": r.text}
        raise HTTPException(status_code=r.status_code, detail=payload)

    return r.json()
