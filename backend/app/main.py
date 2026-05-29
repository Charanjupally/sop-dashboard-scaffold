"""
SOP Operations Dashboard — FastAPI Backend
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import orjson
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.core.cache import init_cache
from app.core.http import close_http_client
from app.api import market, macro, aqi, news, hr, sop, scrapers


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cache()
    yield
    await close_http_client()


app = FastAPI(
    title="SOP Ops Dashboard API",
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────
app.include_router(market.router, prefix="/api/market", tags=["Market"])
app.include_router(macro.router,  prefix="/api/macro",  tags=["Macro"])
app.include_router(aqi.router,    prefix="/api/aqi",    tags=["AQI"])
app.include_router(news.router,   prefix="/api/news",   tags=["News"])
app.include_router(hr.router,     prefix="/api/hr",     tags=["HR"])
app.include_router(sop.router,    prefix="/api/sop",    tags=["SOP"])
app.include_router(scrapers.router, prefix="/api/scrapers", tags=["Scrapers"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
