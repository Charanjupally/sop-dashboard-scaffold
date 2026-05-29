"""
Celery worker — scheduled scans.

Beat schedule (every N minutes):
  - every 1 min  : crypto + FX (cache warm)
  - every 5 min  : AQI, news, HN, HR
  - every 60 min : FRED macro
  - every 5 min  : trigger evaluation → Trello if new
"""
from celery import Celery
from celery.schedules import crontab
import asyncio

from app.core.config import settings

celery_app = Celery(
    "sop_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        "warm-crypto-fx": {
            "task": "app.worker.warm_market",
            "schedule": 60,  # every 60 seconds
        },
        "warm-aqi-news-hr": {
            "task": "app.worker.warm_secondary",
            "schedule": 300,  # every 5 min
        },
        "warm-macro": {
            "task": "app.worker.warm_macro",
            "schedule": crontab(minute=0),  # every hour
        },
        "run-triggers": {
            "task": "app.worker.run_trigger_scan",
            "schedule": 300,  # every 5 min
        },
    },
)


def run_async(coro):
    """Run an async function from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.worker.warm_market")
def warm_market():
    async def _():
        from app.core.cache import init_cache, cached, TTL_CRYPTO, TTL_FX
        from app.api.market import _fetch_crypto, _fetch_fx
        await init_cache()
        await cached("market:crypto", TTL_CRYPTO, _fetch_crypto)
        await cached("market:fx",     TTL_FX,     _fetch_fx)
    run_async(_())


@celery_app.task(name="app.worker.warm_secondary")
def warm_secondary():
    async def _():
        from app.core.cache import init_cache, cached, TTL_AQI, TTL_NEWS, TTL_EDGAR, TTL_CLOCKIFY
        from app.api.aqi  import _fetch_all
        from app.api.news import _fetch_hn_top, _fetch_sec_8k
        from app.api.hr   import _fetch_hr
        await init_cache()
        await cached("aqi:all",        TTL_AQI,      _fetch_all)
        await cached("news:hn",        TTL_NEWS,      _fetch_hn_top)
        await cached("news:sec",       TTL_EDGAR,     _fetch_sec_8k)
        await cached("hr:utilization", TTL_CLOCKIFY,  _fetch_hr)
    run_async(_())


@celery_app.task(name="app.worker.warm_macro")
def warm_macro():
    async def _():
        from app.core.cache import init_cache, cached, TTL_FRED
        from app.api.macro import _fetch_macro
        await init_cache()
        await cached("macro:fred", TTL_FRED, _fetch_macro)
    run_async(_())


@celery_app.task(name="app.worker.run_trigger_scan")
def run_trigger_scan():
    """Re-evaluate triggers and create Trello cards for new ones."""
    async def _():
        from app.core.cache import init_cache, cache_get, cache_set
        from app.api.sop import create_trello_card
        from app.core.trigger import evaluate_all
        from app.core.cache import cached, TTL_CRYPTO, TTL_FX, TTL_FRED, TTL_AQI, TTL_NEWS, TTL_EDGAR, TTL_CLOCKIFY, TTL_NOTION
        from app.api.market import _fetch_crypto, _fetch_fx
        from app.api.macro  import _fetch_macro
        from app.api.aqi    import _fetch_all as _fetch_aqi
        from app.api.news   import _fetch_hn_top, _fetch_sec_8k
        from app.api.hr     import _fetch_hr
        from app.api.sop    import _fetch_sop_registry

        await init_cache()

        snapshot = {
            "crypto": await cached("market:crypto", TTL_CRYPTO,   _fetch_crypto),
            "fx":     await cached("market:fx",     TTL_FX,       _fetch_fx),
            "macro":  await cached("macro:fred",    TTL_FRED,     _fetch_macro),
            "aqi":    await cached("aqi:all",       TTL_AQI,      _fetch_aqi),
            "news":   {
                "hn_stories":  await cached("news:hn",  TTL_NEWS,  _fetch_hn_top),
                "sec_filings": await cached("news:sec", TTL_EDGAR, _fetch_sec_8k),
            },
            "hr":     await cached("hr:utilization", TTL_CLOCKIFY, _fetch_hr),
            "sop":    await cached("sop:registry",   TTL_NOTION,   _fetch_sop_registry),
        }

        triggers = await evaluate_all(snapshot)

        # Track which trigger IDs we've already created Trello cards for
        seen_key = "trello:created_trigger_ids"
        seen = set(await cache_get(seen_key) or [])

        for t in triggers:
            if t.severity == "critical" and t.id not in seen:
                try:
                    await create_trello_card(
                        t.id,
                        f"[SOP TRIGGER] {t.sop_name}",
                        f"**Summary:** {t.summary}\n\n**Source:** {t.source}\n\n**SLA:** {t.sla_hours}h\n\n**Assignee:** {t.assignee}",
                    )
                    seen.add(t.id)
                except Exception:
                    pass

        # Reset seen set each day (simple TTL: 24h)
        await cache_set(seen_key, list(seen), 86400)

    run_async(_())
