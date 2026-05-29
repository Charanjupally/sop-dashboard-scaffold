"""
/api/news — HackerNews top stories + SEC EDGAR recent 8-K filings
"""
from fastapi import APIRouter
from app.core.cache import cached, TTL_NEWS, TTL_EDGAR
from app.core.http import http_get
from app.core.config import settings

router = APIRouter()

HN_BASE    = "https://hacker-news.firebaseio.com/v0"
EDGAR_BASE = "https://efts.sec.gov/LATEST/search-index"


# ── HackerNews ─────────────────────────────────────────
async def _fetch_hn_top(limit: int = 10) -> list[dict]:
    ids = await http_get(f"{HN_BASE}/topstories.json")
    stories = []
    for story_id in ids[:limit]:
        try:
            item = await http_get(f"{HN_BASE}/item/{story_id}.json")
            stories.append({
                "id":     item.get("id"),
                "title":  item.get("title"),
                "url":    item.get("url", ""),
                "score":  item.get("score", 0),
                "by":     item.get("by"),
                "time":   item.get("time"),
            })
        except Exception:
            continue
    return sorted(stories, key=lambda s: s["score"], reverse=True)


# ── SEC EDGAR (recent 8-K filings) ────────────────────
async def _fetch_sec_8k(limit: int = 5) -> list[dict]:
    data = await http_get(
        "https://efts.sec.gov/LATEST/search-index?q=%228-K%22&dateRange=custom&startdt=2024-01-01&forms=8-K",
        headers={
            "User-Agent": settings.SEC_USER_AGENT,
            "Accept": "application/json",
        },
    )
    hits = data.get("hits", {}).get("hits", [])[:limit]
    return [
        {
            "company":    h["_source"].get("display_names", ["Unknown"])[0],
            "form":       h["_source"].get("file_type"),
            "filed_at":   h["_source"].get("file_date"),
            "url":        f"https://www.sec.gov/Archives/edgar/data/{h['_source'].get('entity_id', '')}/",
        }
        for h in hits
    ]


# ── Routes ─────────────────────────────────────────────
@router.get("/hackernews")
async def get_hn():
    return {"stories": await cached("news:hn", TTL_NEWS, _fetch_hn_top)}


@router.get("/sec")
async def get_sec():
    return {"filings": await cached("news:sec", TTL_EDGAR, _fetch_sec_8k)}


@router.get("/snapshot")
async def news_snapshot():
    stories  = await cached("news:hn",  TTL_NEWS,  _fetch_hn_top)
    filings  = await cached("news:sec", TTL_EDGAR, _fetch_sec_8k)
    return {"hn_stories": stories, "sec_filings": filings}
