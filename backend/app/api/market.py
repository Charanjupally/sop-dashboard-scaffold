"""
/api/market — Crypto, FX, Stock prices
"""
from fastapi import APIRouter
from app.core.cache import cached, TTL_CRYPTO, TTL_FX, TTL_STOCK
from app.core.http import http_get
from app.core.config import settings

router = APIRouter()


# ── CoinGecko ──────────────────────────────────────────
async def _fetch_crypto():
    params = {
        "ids": "bitcoin,ethereum,solana",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    if settings.COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = settings.COINGECKO_API_KEY

    data = await http_get(
        "https://api.coingecko.com/api/v3/simple/price",
        params=params,
    )
    return {
        "btc_price": data["bitcoin"]["usd"],
        "btc_change_24h": data["bitcoin"].get("usd_24h_change", 0.0),
        "eth_price": data["ethereum"]["usd"],
        "eth_change_24h": data["ethereum"].get("usd_24h_change", 0.0),
        "sol_price": data["solana"]["usd"],
        "sol_change_24h": data["solana"].get("usd_24h_change", 0.0),
    }


# ── Frankfurter FX ─────────────────────────────────────
async def _fetch_fx():
    latest = await http_get(
        "https://api.frankfurter.app/latest",
        params={"from": "USD", "to": "INR,EUR,GBP,AED"},
    )
    # WoW: fetch 7 days ago for change calculation
    from datetime import date, timedelta
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    historical = await http_get(
        f"https://api.frankfurter.app/{week_ago}",
        params={"from": "USD", "to": "INR"},
    )

    latest_rates = latest.get("rates") or {}
    historical_rates = historical.get("rates") or {}

    inr_now = latest_rates.get("INR")
    inr_prev = historical_rates.get("INR")
    change = None
    if inr_now is not None and inr_prev not in (None, 0):
        change = round(((inr_now - inr_prev) / inr_prev) * 100, 2)

    return {
        "usd_inr": inr_now,
        "usd_inr_change_wow": change,
        "usd_eur": latest_rates.get("EUR"),
        "usd_gbp": latest_rates.get("GBP"),
        "usd_aed": latest_rates.get("AED"),
        "date": latest.get("date"),
    }


# ── Alpha Vantage ──────────────────────────────────────
async def _fetch_stock(symbol: str = "RELIANCE.BSE"):
    data = await http_get(
        "https://www.alphavantage.co/query",
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": settings.ALPHA_VANTAGE_KEY,
        },
    )
    q = data.get("Global Quote", {})
    return {
        "symbol": q.get("01. symbol", symbol),
        "price": float(q.get("05. price", 0)),
        "change_pct": float(q.get("10. change percent", "0%").replace("%", "")),
        "volume": q.get("06. volume"),
    }


# ── Routes ─────────────────────────────────────────────
@router.get("/crypto")
async def get_crypto():
    return await cached("market:crypto", TTL_CRYPTO, _fetch_crypto)


@router.get("/fx")
async def get_fx():
    return await cached("market:fx", TTL_FX, _fetch_fx)


@router.get("/stock/{symbol}")
async def get_stock(symbol: str = "RELIANCE.BSE"):
    key = f"market:stock:{symbol.upper()}"
    return await cached(key, TTL_STOCK, lambda: _fetch_stock(symbol))


@router.get("/snapshot")
async def market_snapshot():
    """Combined snapshot for the dashboard KPI strip."""
    crypto = await cached("market:crypto", TTL_CRYPTO, _fetch_crypto)
    fx     = await cached("market:fx",     TTL_FX,     _fetch_fx)
    return {"crypto": crypto, "fx": fx}
