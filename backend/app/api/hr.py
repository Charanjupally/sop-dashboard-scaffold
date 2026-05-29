"""
/api/hr — Team utilization from Clockify
"""
from datetime import date, timedelta
from fastapi import APIRouter
from app.core.cache import cached, TTL_CLOCKIFY
from app.core.http import http_get
from app.core.config import settings

router = APIRouter()

CLOCKIFY_BASE = "https://api.clockify.me/api/v1"


async def _fetch_members() -> list[dict]:
    headers = {"X-Api-Key": settings.CLOCKIFY_API_KEY}
    members = await http_get(
        f"{CLOCKIFY_BASE}/workspaces/{settings.CLOCKIFY_WORKSPACE_ID}/members",
        headers=headers,
    )
    return members


async def _fetch_time_entries(user_id: str, start: str, end: str) -> float:
    """Return total hours for a user in the given date range."""
    headers = {"X-Api-Key": settings.CLOCKIFY_API_KEY}
    data = await http_get(
        f"{CLOCKIFY_BASE}/workspaces/{settings.CLOCKIFY_WORKSPACE_ID}/user/{user_id}/time-entries",
        headers=headers,
        params={"start": f"{start}T00:00:00Z", "end": f"{end}T23:59:59Z", "page-size": 200},
    )
    total_seconds = 0
    for entry in data:
        duration = entry.get("timeInterval", {}).get("duration", "")
        # Duration is ISO 8601 e.g. PT8H30M
        if duration.startswith("PT"):
            import re
            h = int(re.search(r"(\d+)H", duration).group(1)) if "H" in duration else 0
            m = int(re.search(r"(\d+)M", duration).group(1)) if "M" in duration else 0
            total_seconds += h * 3600 + m * 60
    return round(total_seconds / 3600, 1)


async def _fetch_hr():
    start = (date.today() - timedelta(days=date.today().weekday())).isoformat()  # Monday
    end   = date.today().isoformat()
    max_hours = 40.0

    try:
        members = await _fetch_members()
    except Exception:
        # Return mock data when Clockify is not configured
        return {
            "members": [
                {"id": "1", "name": "Arjun M.",  "hours_this_week": 38.0, "utilization_pct": 95.0},
                {"id": "2", "name": "Priya K.",  "hours_this_week": 32.0, "utilization_pct": 80.0},
                {"id": "3", "name": "Vikram S.", "hours_this_week": 26.0, "utilization_pct": 65.0},
                {"id": "4", "name": "Divya R.",  "hours_this_week": 40.0, "utilization_pct": 100.0},
            ],
            "source": "mock",
        }

    result = []
    for m in members[:10]:
        uid  = m["id"]
        name = m.get("name", uid)
        try:
            hours = await _fetch_time_entries(uid, start, end)
        except Exception:
            hours = 0.0
        result.append({
            "id":   uid,
            "name": name,
            "hours_this_week": hours,
            "utilization_pct": round(min((hours / max_hours) * 100, 100), 1),
        })

    return {"members": result, "source": "clockify"}


@router.get("/")
async def get_hr():
    return await cached("hr:utilization", TTL_CLOCKIFY, _fetch_hr)
