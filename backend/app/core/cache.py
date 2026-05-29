"""
Redis cache layer.

TTL constants match the refresh cadence of each upstream source:
    - Crypto / FX   → 60 s  (volatile, but we don't want to hammer free tiers)
    - Stock prices  → 300 s (Alpha Vantage free: 25 calls/day)
    - AQI           → 300 s (good enough for WFH decisions)
    - Weather       → 600 s
    - FRED macro    → 3600 s (monthly releases)
    - HackerNews    → 300 s
    - SEC EDGAR     → 1800 s
    - Notion/Airtable → 300 s
    - HR / Clockify → 600 s
"""
from datetime import datetime, timezone
import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

# ── TTL constants (seconds) ───────────────────────────
TTL_CRYPTO    = 60
TTL_FX        = 60
TTL_STOCK     = 300
TTL_AQI       = 300
TTL_WEATHER   = 600
TTL_FRED      = 3_600
TTL_NEWS      = 300
TTL_EDGAR     = 1_800
TTL_NOTION    = 300
TTL_AIRTABLE  = 300
TTL_CLOCKIFY  = 600
TTL_TRIGGER   = 60   # trigger evaluation result

# Longer-lived widget sources use a soft TTL for the stale badge and a larger
# hard TTL so the UI can keep showing old data until the next refresh cycle.
TTL_WORLD_BANK   = 86_400
TTL_REDDIT       = 900
TTL_WHO          = 86_400
TTL_RANDOM_USER  = 3_600
TTL_WIKIPEDIA    = 86_400
TTL_REMOTEOK     = 21_600
TTL_ALPHA_CANDLE = 86_400
TTL_USAJOBS      = 3_600
TTL_NEWSAPI      = 900

_client: aioredis.Redis | None = None


async def init_cache() -> None:
    global _client
    _client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


def get_cache() -> aioredis.Redis:
    if _client is None:
        raise RuntimeError("Cache not initialised — call init_cache() first")
    return _client


async def cache_get(key: str) -> Any | None:
    raw = await get_cache().get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int) -> None:
    await get_cache().set(key, json.dumps(value), ex=ttl)


async def cached(key: str, ttl: int, fn):
    """
    Simple async cache-aside helper.

    Usage:
        data = await cached("crypto:btc", TTL_CRYPTO, lambda: fetch_btc())
    """
    hit = await cache_get(key)
    if hit is not None:
        return hit
    result = await fn()
    await cache_set(key, result, ttl)
    return result


async def cached_record(key: str, ttl: int, fn, *, hard_ttl: int | None = None) -> dict[str, Any]:
    """Return a cached widget payload plus UI metadata.

    The value stored in Redis keeps a timestamp so the frontend can show a
    per-widget "Last updated" label and an amber stale badge when the payload
    is older than the widget's soft TTL.
    """
    hit = await cache_get(key)
    if isinstance(hit, dict) and "data" in hit and "cached_at" in hit:
        cached_at_raw = hit["cached_at"]
        cached_at = datetime.fromisoformat(cached_at_raw)
        age_seconds = max(0.0, (datetime.now(timezone.utc) - cached_at).total_seconds())
        return {
            "data": hit["data"],
            "meta": {
                "updated_at": cached_at_raw,
                "ttl_seconds": ttl,
                "age_seconds": age_seconds,
                "is_stale": age_seconds > ttl,
            },
        }

    result = await fn()
    cached_at = datetime.now(timezone.utc).isoformat()
    await cache_set(
        key,
        {
            "data": result,
            "cached_at": cached_at,
        },
        hard_ttl or max(ttl * 24, ttl + 3600),
    )
    return {
        "data": result,
        "meta": {
            "updated_at": cached_at,
            "ttl_seconds": ttl,
            "age_seconds": 0.0,
            "is_stale": False,
        },
    }
