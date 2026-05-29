"""
/api/sop — SOP registry (Notion), Airtable CRM, Trello card creation,
            and the master trigger evaluation endpoint.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import logging

from fastapi import APIRouter, HTTPException
from app.core.cache import (
    cached,
    cached_record,
    TTL_NOTION,
    TTL_AIRTABLE,
    TTL_TRIGGER,
    TTL_CRYPTO,
    TTL_FX,
    TTL_FRED,
    TTL_AQI,
    TTL_NEWS,
    TTL_EDGAR,
    TTL_CLOCKIFY,
    TTL_WORLD_BANK,
    TTL_REDDIT,
    TTL_WHO,
    TTL_RANDOM_USER,
    TTL_WIKIPEDIA,
    TTL_REMOTEOK,
    TTL_ALPHA_CANDLE,
    TTL_USAJOBS,
    TTL_NEWSAPI,
    cache_get,
    cache_set,
)
from app.core.http import http_get
from app.core.config import settings
from app.core.trigger import evaluate_all

router = APIRouter()
logger = logging.getLogger(__name__)

NOTION_BASE   = "https://api.notion.com/v1"
NOTION_HEADERS = lambda: {
    "Authorization": f"Bearer {settings.NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

TRELLO_BASE = "https://api.trello.com/1"


# ── Notion SOP Registry ────────────────────────────────
async def _fetch_sop_registry() -> dict:
    if not settings.NOTION_TOKEN:
        return {"sops": _mock_sops(), "stale_sops": [], "source": "mock"}

    try:
        data = await http_get(
            f"{NOTION_BASE}/databases/{settings.NOTION_DB_SOP}/query",
            headers=NOTION_HEADERS(),
        )
    except Exception as exc:
        logger.warning("Falling back to mock SOP registry: %s", exc)
        return {"sops": _mock_sops(), "stale_sops": [], "source": "mock"}

    sops = []
    stale = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.TRIGGER_SOP_STALE_DAYS)

    for page in data.get("results", []):
        props = page.get("properties", {})
        title_blocks = props.get("Name", {}).get("title", [])
        title = "".join(b.get("plain_text", "") for b in title_blocks)
        status = props.get("Status", {}).get("select", {}).get("name", "Draft")
        last_reviewed_str = props.get("Last Reviewed", {}).get("date", {})
        last_reviewed = last_reviewed_str.get("start") if last_reviewed_str else None

        sop = {
            "id":            page["id"],
            "title":         title,
            "status":        status,
            "last_reviewed": last_reviewed,
            "notion_url":    page.get("url"),
        }
        sops.append(sop)

        if last_reviewed:
            dt = datetime.fromisoformat(last_reviewed.replace("Z", "+00:00"))
            if dt < cutoff:
                stale.append(sop)

    return {"sops": sops, "stale_sops": stale, "source": "notion"}


def _mock_sops():
    return [
        {"id": "1", "title": "Treasury Reserve Review SOP", "status": "Published", "last_reviewed": "2024-11-01"},
        {"id": "2", "title": "Cross-border Invoicing SOP",  "status": "Published", "last_reviewed": "2024-10-15"},
        {"id": "3", "title": "Pricing SOP v2",              "status": "Review",    "last_reviewed": "2024-10-01"},
        {"id": "4", "title": "Crisis Comms SOP",            "status": "Review",    "last_reviewed": "2025-01-10"},
        {"id": "5", "title": "WFH Advisory SOP",            "status": "Published", "last_reviewed": "2025-02-20"},
        {"id": "6", "title": "Payroll Review SOP",          "status": "Draft",     "last_reviewed": None},
        {"id": "7", "title": "Vendor Onboarding SOP",       "status": "Draft",     "last_reviewed": None},
        {"id": "8", "title": "COVID WFH SOP",               "status": "Retired",   "last_reviewed": "2023-12-01"},
    ]


# ── Trello — create urgent card ────────────────────────
async def create_trello_card(trigger_id: str, title: str, description: str) -> dict:
    if not settings.TRELLO_API_KEY:
        return {"mock": True, "card_id": "mock-123"}

    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TRELLO_BASE}/cards",
            params={
                "key":   settings.TRELLO_API_KEY,
                "token": settings.TRELLO_TOKEN,
                "idList": settings.TRELLO_LIST_URGENT,
                "name":  title[:512],
                "desc":  description[:16000],
                "pos":   "top",
                "urlSource": None,
            },
        )
        resp.raise_for_status()
        return resp.json()


# ── Master trigger endpoint ────────────────────────────
@router.get("/triggers")
async def get_triggers():
    """
    Aggregates all data sources and runs the trigger rule engine.
    Returns the list of fired triggers (the morning action queue).
    """
    # Check cache first
    cache_key = "sop:triggers:v4"
    cached_result = await cache_get(cache_key)
    if cached_result:
        return cached_result

    # Import lazily to avoid circular imports at module load
    from app.api.market import _fetch_crypto, _fetch_fx
    from app.api.macro  import _fetch_macro
    from app.api.aqi    import _fetch_all as _fetch_aqi
    from app.api.news   import _fetch_hn_top, _fetch_sec_8k
    from app.api.hr     import _fetch_hr
    from app.api.expanded import (
        _fetch_world_bank_gdp,
        _fetch_reddit_sentiment,
        _fetch_who_health,
        _fetch_randomuser_hr,
        _fetch_wikipedia_pageviews,
        _fetch_remoteok_jobs,
        _fetch_alpha_vantage_candles,
        _fetch_usajobs_compliance,
        _fetch_newsapi_business_india,
    )

    # Gather all data (cached individually)
    crypto      = await cached_record("market:crypto", TTL_CRYPTO,  _fetch_crypto)
    fx          = await cached_record("market:fx",     TTL_FX,      _fetch_fx)
    macro       = await cached_record("macro:fred",    TTL_FRED,    _fetch_macro)
    aqi         = await cached_record("aqi:all",       TTL_AQI,     _fetch_aqi)
    hn          = await cached_record("news:hn",       TTL_NEWS,    _fetch_hn_top)
    filings     = await cached_record("news:sec",      TTL_EDGAR,   _fetch_sec_8k)
    hr          = await cached_record("hr:utilization",TTL_CLOCKIFY,_fetch_hr)
    sop_reg     = await cached_record("sop:registry",  TTL_NOTION,  _fetch_sop_registry)
    world_bank  = await cached_record("world_bank:gdp:v3", TTL_WORLD_BANK, _fetch_world_bank_gdp)
    reddit      = await cached_record("reddit:entrepreneur", TTL_REDDIT, _fetch_reddit_sentiment)
    who         = await cached_record("who:ncd", TTL_WHO, _fetch_who_health)
    random_hr   = await cached_record("hr:randomuser", TTL_RANDOM_USER, _fetch_randomuser_hr)
    wikipedia   = await cached_record("wiki:pageviews", TTL_WIKIPEDIA, _fetch_wikipedia_pageviews)
    remoteok    = await cached_record("remoteok:jobs", TTL_REMOTEOK, _fetch_remoteok_jobs)
    alpha       = await cached_record("alpha:reliance", TTL_ALPHA_CANDLE, _fetch_alpha_vantage_candles)
    usajobs     = await cached_record("usajobs:compliance", TTL_USAJOBS, _fetch_usajobs_compliance)
    newsapi     = await cached_record("newsapi:india-business", TTL_NEWSAPI, _fetch_newsapi_business_india)

    news_meta = {
        "updated_at": max(hn["meta"]["updated_at"], filings["meta"]["updated_at"]),
        "ttl_seconds": min(TTL_NEWS, TTL_EDGAR),
        "age_seconds": max(hn["meta"]["age_seconds"], filings["meta"]["age_seconds"]),
        "is_stale": bool(hn["meta"]["is_stale"] or filings["meta"]["is_stale"]),
    }

    snapshot = {
        "crypto":      crypto,
        "fx":          fx,
        "macro":       macro,
        "aqi":         aqi,
        "news":        {"data": {"hn_stories": hn["data"], "sec_filings": filings["data"]}, "meta": news_meta},
        "hr":          hr,
        "sop":         sop_reg,
        "world_bank":  world_bank,
        "reddit":      reddit,
        "who":         who,
        "random_user": random_hr,
        "wikipedia":   wikipedia,
        "remoteok":    remoteok,
        "alpha_vantage": alpha,
        "usajobs":     usajobs,
        "newsapi":     newsapi,
    }

    triggers = await evaluate_all({
        "crypto": crypto["data"],
        "fx": fx["data"],
        "macro": macro["data"],
        "aqi": aqi["data"],
        "news": {"hn_stories": hn["data"], "sec_filings": filings["data"]},
        "hr": hr["data"],
        "sop": sop_reg["data"],
        "world_bank": world_bank["data"],
        "reddit": reddit["data"],
        "who": who["data"],
        "random_user": random_hr["data"],
        "wikipedia": wikipedia["data"],
        "remoteok": remoteok["data"],
        "alpha_vantage": alpha["data"],
        "usajobs": usajobs["data"],
        "newsapi": newsapi["data"],
    })
    result = {
        "triggers":   [t.__dict__ for t in triggers],
        "snapshot":   snapshot,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    await cache_set(cache_key, result, TTL_TRIGGER)
    return result


@router.get("/registry")
async def get_sop_registry():
    return await cached("sop:registry", TTL_NOTION, _fetch_sop_registry)


@router.post("/trello-card")
async def post_trello_card(trigger_id: str, title: str, description: str = ""):
    try:
        card = await create_trello_card(trigger_id, title, description)
        return {"success": True, "card": card}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
