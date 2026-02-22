import os
import asyncio
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
    # balldontlie: Authorization: <API_KEY>
    return {"Authorization": BDL_API_KEY}

async def bdl_get(path: str, params=None, max_retries: int = 4):
    """
    GET con retry/backoff cuando hay 429 (rate limit) o 5xx.
    """
    url = f"{BDL_BASE_URL}{path}"
    headers = _headers()

    backoff = 2  # segundos
    async with httpx.AsyncClient(timeout=25.0) as client:
        for attempt in range(max_retries + 1):
            r = await client.get(url, headers=headers, params=params)

            # ✅ Rate limit
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                wait_s = None
                if retry_after and retry_after.isdigit():
                    wait_s = int(retry_after)
                else:
                    wait_s = backoff

                if attempt >= max_retries:
                    raise HTTPException(
                        status_code=429,
                        detail={"error": "Too many requests (rate limit).", "retry_after_seconds": wait_s},
                    )

                await asyncio.sleep(wait_s)
                backoff = min(backoff * 2, 30)
                continue

            # ✅ Errores temporales del servidor
            if 500 <= r.status_code <= 599:
                if attempt >= max_retries:
                    try:
                        payload = r.json()
                    except Exception:
                        payload = {"error": r.text}
                    raise HTTPException(status_code=r.status_code, detail=payload)

                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue

            # ❌ Otros errores (401/403/etc.)
            if r.status_code >= 400:
                try:
                    payload = r.json()
                except Exception:
                    payload = {"error": r.text}
                raise HTTPException(status_code=r.status_code, detail=payload)

            return r.json()

    raise HTTPException(status_code=500, detail="Unexpected error in bdl_get")
