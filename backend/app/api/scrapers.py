from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core.scraper_status import build_scraper_health_rows

router = APIRouter()


@router.get("/status")
async def scraper_status():
    try:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "rows": build_scraper_health_rows(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
