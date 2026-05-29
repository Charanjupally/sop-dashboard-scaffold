#!/usr/bin/env bash
# scripts/health_check.sh
# Quick smoke-test of all data source endpoints.
# Usage: bash scripts/health_check.sh

set -euo pipefail
source .env 2>/dev/null || true

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[0;33m'; NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC}  $1"; }
fail() { echo -e "${RED}✗${NC}  $1 — $2"; }
warn() { echo -e "${YELLOW}?${NC}  $1 — $2"; }

echo ""
echo "── SOP Dashboard · Source Health Check ─────────────────"
echo ""

# ── No-key sources ────────────────────────────────────
curl -sf "https://api.frankfurter.app/latest?from=USD&to=INR" > /dev/null && pass "Frankfurter FX" || fail "Frankfurter FX" "unreachable"
curl -sf "https://api.open-meteo.com/v1/forecast?latitude=17.4&longitude=78.5&current=temperature_2m" > /dev/null && pass "Open-Meteo weather" || fail "Open-Meteo" "unreachable"
curl -sf "https://hacker-news.firebaseio.com/v0/topstories.json" > /dev/null && pass "HackerNews" || fail "HackerNews" "unreachable"
curl -sf -H "User-Agent: ${SEC_USER_AGENT:-SOP/1.0}" "https://efts.sec.gov/LATEST/search-index?q=%228-K%22&forms=8-K" > /dev/null && pass "SEC EDGAR" || fail "SEC EDGAR" "unreachable"

# ── Key-gated sources ─────────────────────────────────
if [ -n "${COINGECKO_API_KEY:-}" ]; then
  curl -sf "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&x_cg_demo_api_key=${COINGECKO_API_KEY}" > /dev/null && pass "CoinGecko (keyed)" || fail "CoinGecko" "bad key or rate limit"
else
  curl -sf "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd" > /dev/null && pass "CoinGecko (public)" || warn "CoinGecko" "no key set — may be rate-limited"
fi

if [ -n "${FRED_API_KEY:-}" ]; then
  curl -sf "https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key=${FRED_API_KEY}&file_type=json&limit=1" > /dev/null && pass "FRED (CPI)" || fail "FRED" "bad key"
else
  warn "FRED" "FRED_API_KEY not set"
fi

if [ -n "${AQICN_TOKEN:-}" ]; then
  curl -sf "https://api.waqi.info/feed/hyderabad/?token=${AQICN_TOKEN}" > /dev/null && pass "AQICN" || fail "AQICN" "bad token"
else
  warn "AQICN" "AQICN_TOKEN not set"
fi

if [ -n "${ALPHA_VANTAGE_KEY:-}" ]; then
  curl -sf "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=${ALPHA_VANTAGE_KEY}" > /dev/null && pass "Alpha Vantage" || fail "Alpha Vantage" "bad key"
else
  warn "Alpha Vantage" "ALPHA_VANTAGE_KEY not set"
fi

[ -n "${NOTION_TOKEN:-}" ]     && pass "Notion token set"     || warn "Notion"     "NOTION_TOKEN not set"
[ -n "${AIRTABLE_TOKEN:-}" ]   && pass "Airtable token set"   || warn "Airtable"   "AIRTABLE_TOKEN not set"
[ -n "${CLOCKIFY_API_KEY:-}" ] && pass "Clockify key set"     || warn "Clockify"   "CLOCKIFY_API_KEY not set"
[ -n "${TRELLO_API_KEY:-}" ]   && pass "Trello keys set"      || warn "Trello"     "TRELLO_API_KEY not set"

# ── Local services ────────────────────────────────────
echo ""
echo "── Local services ────────────────────────────────────────"
curl -sf "http://localhost:8000/health" > /dev/null && pass "FastAPI backend (8000)" || fail "FastAPI backend" "not running — docker compose up"
curl -sf "http://localhost:3000" > /dev/null        && pass "Next.js frontend (3000)" || fail "Next.js frontend" "not running"
redis-cli -u "${REDIS_URL:-redis://localhost:6379}" ping > /dev/null 2>&1 && pass "Redis" || fail "Redis" "not running"

echo ""
echo "────────────────────────────────────────────────────────"
echo "Run:  docker compose up --build   to start all services"
echo ""
