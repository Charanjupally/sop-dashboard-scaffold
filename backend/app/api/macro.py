"""
/api/macro — FRED economic indicators (CPI, unemployment, fed funds rate)
"""
from fastapi import APIRouter
from app.core.cache import cached, TTL_FRED
from app.core.http import http_get
from app.core.config import settings

router = APIRouter()

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


async def _fred(series_id: str, limit: int = 2) -> list[dict]:
    data = await http_get(
        FRED_BASE,
        params={
            "series_id": series_id,
            "api_key": settings.FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        },
    )
    return data.get("observations", [])


async def _fetch_macro():
    cpi_obs   = await _fred("CPIAUCSL", 2)
    unemp_obs = await _fred("UNRATE",   1)
    fed_obs   = await _fred("FEDFUNDS", 1)

    cpi_latest  = float(cpi_obs[0]["value"])  if cpi_obs   else None
    cpi_prior   = float(cpi_obs[1]["value"])  if len(cpi_obs) > 1 else None
    cpi_mom     = round(cpi_latest - cpi_prior, 3) if (cpi_latest and cpi_prior) else None

    return {
        "cpi_latest":  cpi_latest,
        "cpi_prior":   cpi_prior,
        "cpi_mom":     cpi_mom,
        "cpi_date":    cpi_obs[0]["date"]   if cpi_obs   else None,
        "unemployment": float(unemp_obs[0]["value"]) if unemp_obs else None,
        "fed_funds":    float(fed_obs[0]["value"])   if fed_obs   else None,
    }


@router.get("/")
async def get_macro():
    return await cached("macro:fred", TTL_FRED, _fetch_macro)
