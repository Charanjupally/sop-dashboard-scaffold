"""Additional dashboard data sources for the production widget set."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
import re

from app.core.config import settings
from app.core.http import http_get


def _ua(label: str) -> dict[str, str]:
    return {"User-Agent": f"ElevateBox SOP Dashboard/1.0 ({label}) ops@example.com"}


def _safe_float(value, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value, default: int | None = None) -> int | None:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _parse_salary_range(text: str | None) -> dict[str, int | None]:
    if not text:
        return {"min": None, "max": None, "mid": None}
    nums = [int(n.replace(",", "")) for n in re.findall(r"\$?([0-9][0-9,]+)", text)]
    if not nums:
        return {"min": None, "max": None, "mid": None}
    if len(nums) == 1:
        return {"min": nums[0], "max": nums[0], "mid": nums[0]}
    low, high = min(nums[0], nums[1]), max(nums[0], nums[1])
    return {"min": low, "max": high, "mid": (low + high) // 2}


def _demo_world_bank() -> dict:
    return {
        "bars": [
            {"country": "IND", "country_name": "India", "year": 2023, "gdp": 3_700_000_000_000},
            {"country": "CHN", "country_name": "China", "year": 2023, "gdp": 17_700_000_000_000},
            {"country": "USA", "country_name": "United States", "year": 2023, "gdp": 27_700_000_000_000},
            {"country": "GBR", "country_name": "United Kingdom", "year": 2023, "gdp": 3_340_000_000_000},
        ],
        "trigger_hint": "Inflation deviates >2σ from the 10-year mean → Pricing Review SOP",
        "source": "World Bank",
    }


def _demo_reddit() -> dict:
    return {
        "posts": [
            {"title": "What is one thing you wish you knew before starting a business?", "score": 1820, "comments": 314, "url": "https://reddit.com"},
            {"title": "How do you handle customer complaints at scale?", "score": 1330, "comments": 201, "url": "https://reddit.com"},
            {"title": "The hardest part of building a startup is still sales", "score": 1090, "comments": 176, "url": "https://reddit.com"},
            {"title": "What tools save you the most time each week?", "score": 870, "comments": 122, "url": "https://reddit.com"},
            {"title": "Failed product launch postmortem", "score": 640, "comments": 94, "url": "https://reddit.com"},
        ],
        "trigger_hint": "Complaint spike >2x rolling average → Competitive Intelligence Briefing SOP",
        "source": "Reddit",
    }


def _demo_who() -> dict:
    return {
        "cells": [
            {"country": "India", "value": 18.2, "year": 2023},
            {"country": "United States", "value": 14.9, "year": 2023},
            {"country": "United Kingdom", "value": 16.4, "year": 2023},
            {"country": "Brazil", "value": 21.7, "year": 2023},
            {"country": "South Africa", "value": 24.1, "year": 2023},
            {"country": "Japan", "value": 12.8, "year": 2023},
        ],
        "trigger_hint": "Indicator worsens QoQ → Compliance Audit SOP",
        "source": "WHO",
    }


def _demo_randomuser() -> dict:
    return {
        "employees": [
            {"avatar": None, "name": "Ava Patel", "country": "India", "age": 29, "gender": "female"},
            {"avatar": None, "name": "Noah Smith", "country": "United States", "age": 34, "gender": "male"},
            {"avatar": None, "name": "Ethan Cole", "country": "United Kingdom", "age": 27, "gender": "male"},
        ],
        "gender_distribution": {"female": 1, "male": 2},
        "country_distribution": {"India": 1, "United States": 1, "United Kingdom": 1},
        "trigger_hint": "Use this only as a placeholder until Airtable HRIS is wired in production",
        "source": "RandomUser",
    }


def _demo_wikipedia() -> dict:
    return {
        "series": [
            {"article": "OpenAI", "points": [{"week": "2026-W18", "views": 120000}, {"week": "2026-W19", "views": 136000}, {"week": "2026-W20", "views": 149000}]},
            {"article": "Anthropic", "points": [{"week": "2026-W18", "views": 86000}, {"week": "2026-W19", "views": 92000}, {"week": "2026-W20", "views": 101000}]},
        ],
        "trigger_hint": "Views >2x the 30-day rolling mean → Reputation Audit SOP",
        "source": "Wikipedia",
    }


def _demo_remoteok() -> dict:
    return {
        "jobs": [
            {"title": "Senior Product Manager", "company": "Acme AI", "posted_at": "2026-05-29", "salary_min": 180000, "salary_max": 220000, "salary_mid": 200000, "tag_count": 4, "tags": ["product", "ai", "remote", "senior"]},
            {"title": "Compliance Analyst", "company": "FinOps", "posted_at": "2026-05-28", "salary_min": 120000, "salary_max": 160000, "salary_mid": 140000, "tag_count": 3, "tags": ["compliance", "finance", "remote"]},
        ],
        "trigger_hint": "Used quarterly to trigger Market Salary Benchmark SOP",
        "source": "RemoteOK",
    }


def _demo_alpha(symbol: str) -> dict:
    return {
        "symbol": symbol,
        "daily_change_pct": 0.0,
        "candles": [
            {"date": "2026-05-22", "open": 2820, "high": 2855, "low": 2792, "close": 2838, "volume": 2100000},
            {"date": "2026-05-23", "open": 2838, "high": 2862, "low": 2810, "close": 2844, "volume": 1950000},
            {"date": "2026-05-26", "open": 2844, "high": 2870, "low": 2830, "close": 2864, "volume": 2010000},
        ],
        "trigger_hint": "Equity moves >5% → Investor Update SOP",
        "source": "Alpha Vantage",
    }


def _demo_usajobs() -> dict:
    return {
        "jobs": [
            {"title": "Compliance Program Analyst", "agency": "Department of Treasury", "location": "Washington, DC", "published": "2026-05-28", "url": "https://usajobs.gov"},
            {"title": "Risk Management Specialist", "agency": "Department of Defense", "location": "Washington, DC", "published": "2026-05-27", "url": "https://usajobs.gov"},
        ],
        "trigger_hint": "New relevant posting → Capture Management SOP",
        "source": "USAJOBS",
    }


def _demo_newsapi() -> dict:
    return {
        "articles": [
            {"title": "India business confidence improves as exports rise", "source": "Reuters", "url": None, "published_at": "2026-05-29", "description": None},
            {"title": "Banks warn on property sector slowdown", "source": "Bloomberg", "url": None, "published_at": "2026-05-29", "description": None},
            {"title": "Manufacturing orders strengthen in May", "source": "Moneycontrol", "url": None, "published_at": "2026-05-29", "description": None},
        ],
        "trigger_hint": "Client name appears with negative sentiment keywords → Crisis Comms SOP",
        "source": "NewsAPI",
    }


async def _fetch_world_bank_gdp() -> dict:
    try:
        data = await http_get(
            "https://api.worldbank.org/v2/country/IND;CHN;USA;GBR/indicator/NY.GDP.MKTP.CD",
            params={"format": "json", "mrv": 3, "per_page": 12},
            headers=_ua("world-bank-gdp"),
        )
        rows = data[1] if isinstance(data, list) and len(data) > 1 else []
        latest: dict[str, dict] = {}
        for row in rows:
            country = row.get("countryiso3code") or (row.get("country") or {}).get("id")
            year = _safe_int(row.get("date"))
            value = _safe_float(row.get("value"))
            if country in {"IND", "CHN", "USA", "GBR"} and year and value is not None:
                current = latest.get(country)
                if current is None or year > current["year"]:
                    latest[country] = {
                        "country": country,
                        "country_name": (row.get("country") or {}).get("value", country),
                        "year": year,
                        "gdp": value,
                    }
        ordered = [latest.get(code, {"country": code, "country_name": code, "year": None, "gdp": None}) for code in ["IND", "CHN", "USA", "GBR"]]
        return {"bars": ordered, "trigger_hint": "Inflation deviates >2σ from the 10-year mean → Pricing Review SOP", "source": "World Bank"}
    except Exception:
        return _demo_world_bank()


async def _fetch_reddit_sentiment() -> dict:
    try:
        data = await http_get(
            "https://www.reddit.com/r/Entrepreneur/top.json",
            params={"limit": 25, "t": "day"},
            headers=_ua("reddit-entrepreneur"),
        )
        posts = []
        for child in data.get("data", {}).get("children", [])[:5]:
            item = child.get("data", {})
            posts.append({
                "title": item.get("title", "Untitled"),
                "score": item.get("score", 0),
                "comments": item.get("num_comments", 0),
                "url": f"https://reddit.com{item.get('permalink', '')}",
            })
        if not posts:
            raise ValueError("no reddit posts")
        return {"posts": posts, "trigger_hint": "Complaint spike >2x rolling average → Competitive Intelligence Briefing SOP", "source": "Reddit"}
    except Exception:
        return _demo_reddit()


async def _fetch_who_health() -> dict:
    try:
        data = await http_get("https://ghoapi.azureedge.net/api/NCDMORT3070", headers=_ua("who-ncd-mortality"))
        rows = data.get("value", []) if isinstance(data, dict) else []
        latest_by_country: dict[str, dict] = {}
        for row in rows:
            country = row.get("SpatialDim") or row.get("SpatialDimDisplayText") or row.get("SpatialDimName")
            value = _safe_float(row.get("NumericValue"))
            year = _safe_int(row.get("TimeDim")) or _safe_int((row.get("TimeDimDisplayText") or "")[:4])
            if country and value is not None:
                current = latest_by_country.get(country)
                if current is None or (year is not None and (current.get("year") is None or year > current["year"])):
                    latest_by_country[country] = {"country": country, "value": value, "year": year}
        cells = sorted(latest_by_country.values(), key=lambda x: (x["value"] is None, x.get("value", 0)), reverse=True)[:24]
        if not cells:
            raise ValueError("no who data")
        return {"cells": cells, "trigger_hint": "Indicator worsens QoQ → Compliance Audit SOP", "source": "WHO"}
    except Exception:
        return _demo_who()


async def _fetch_randomuser_hr() -> dict:
    try:
        data = await http_get("https://randomuser.me/api/", params={"results": 20, "nat": "us,in,gb"}, headers=_ua("randomuser-hr"))
        employees = []
        genders = Counter()
        countries = Counter()
        for person in data.get("results", []):
            name = person.get("name", {})
            location = person.get("location", {})
            employees.append({
                "avatar": person.get("picture", {}).get("thumbnail"),
                "name": f"{name.get('first', '')} {name.get('last', '')}".strip(),
                "country": location.get("country", "Unknown"),
                "age": person.get("dob", {}).get("age"),
                "gender": person.get("gender"),
            })
            genders[person.get("gender", "unknown")] += 1
            countries[location.get("country", "Unknown")] += 1
        if not employees:
            raise ValueError("no randomuser data")
        return {
            "employees": employees,
            "gender_distribution": dict(genders),
            "country_distribution": dict(countries),
            "trigger_hint": "Use this only as a placeholder until Airtable HRIS is wired in production",
            "source": "RandomUser",
        }
    except Exception:
        return _demo_randomuser()


WIKIPEDIA_ARTICLES = ["OpenAI", "Anthropic"]


async def _fetch_wikipedia_pageviews() -> dict:
    try:
        end = date.today()
        start = end - timedelta(days=56)
        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")
        series: list[dict] = []
        for article in WIKIPEDIA_ARTICLES:
            url_title = article.replace(" ", "_")
            data = await http_get(
                f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/{url_title}/daily/{start_str}/{end_str}",
                headers=_ua("wikipedia-pageviews"),
            )
            buckets: dict[str, int] = defaultdict(int)
            for row in data.get("items", []):
                day = row.get("timestamp", "")[:8]
                if len(day) == 8:
                    year, week, _ = date(int(day[:4]), int(day[4:6]), int(day[6:8])).isocalendar()
                    buckets[f"{year}-W{week:02d}"] += int(row.get("views", 0))
            series.append({"article": article, "points": [{"week": week, "views": views} for week, views in sorted(buckets.items())]})
        if not series or not series[0]["points"]:
            raise ValueError("no wikipedia data")
        return {"series": series, "trigger_hint": "Views >2x the 30-day rolling mean → Reputation Audit SOP", "source": "Wikipedia"}
    except Exception:
        return _demo_wikipedia()


async def _fetch_remoteok_jobs() -> dict:
    try:
        data = await http_get("https://remoteok.com/api", headers=_ua("remoteok-jobs"))
        jobs = []
        for row in data[1:12] if isinstance(data, list) and len(data) > 1 else []:
            salary = _parse_salary_range(row.get("salary"))
            tags = row.get("tags") or []
            jobs.append({
                "title": row.get("position") or row.get("title") or "Unknown role",
                "company": row.get("company") or "Unknown",
                "posted_at": row.get("date"),
                "salary_min": salary["min"],
                "salary_max": salary["max"],
                "salary_mid": salary["mid"],
                "tag_count": len(tags),
                "tags": tags[:5],
            })
        if not jobs:
            raise ValueError("no remoteok data")
        return {"jobs": jobs, "trigger_hint": "Used quarterly to trigger Market Salary Benchmark SOP", "source": "RemoteOK"}
    except Exception:
        return _demo_remoteok()


async def _fetch_alpha_vantage_candles(symbol: str = "RELIANCE.BSE") -> dict:
    if not settings.ALPHA_VANTAGE_KEY:
        return _demo_alpha(symbol)
    try:
        data = await http_get(
            "https://www.alphavantage.co/query",
            params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": settings.ALPHA_VANTAGE_KEY},
            headers=_ua("alpha-vantage-candles"),
        )
        series = data.get("Time Series (Daily)", {}) if isinstance(data, dict) else {}
        candles = []
        for day in sorted(series.keys(), reverse=True)[:30][::-1]:
            row = series[day]
            candles.append({
                "date": day,
                "open": _safe_float(row.get("1. open"), 0.0) or 0.0,
                "high": _safe_float(row.get("2. high"), 0.0) or 0.0,
                "low": _safe_float(row.get("3. low"), 0.0) or 0.0,
                "close": _safe_float(row.get("4. close"), 0.0) or 0.0,
                "volume": _safe_int(row.get("5. volume"), 0) or 0,
            })
        if len(candles) < 2:
            raise ValueError("no alpha candles")
        daily_change_pct = 0.0
        if candles[-2]["close"]:
            daily_change_pct = round(((candles[-1]["close"] - candles[-2]["close"]) / candles[-2]["close"]) * 100, 2)
        return {"symbol": symbol, "daily_change_pct": daily_change_pct, "candles": candles, "trigger_hint": "Equity moves >5% → Investor Update SOP", "source": "Alpha Vantage"}
    except Exception:
        return _demo_alpha(symbol)


async def _fetch_usajobs_compliance() -> dict:
    try:
        data = await http_get(
            "https://data.usajobs.gov/api/Search",
            params={"Keyword": "compliance", "LocationName": "Washington,DC"},
            headers={"Authorization-Key": settings.USAJOBS_KEY, "User-Agent": settings.SEC_USER_AGENT, "Accept": "application/json"},
        )
        jobs = []
        for item in data.get("SearchResult", {}).get("SearchResultItems", [])[:10]:
            job = item.get("MatchedObjectDescriptor", {})
            locations = job.get("PositionLocation", [])
            jobs.append({
                "title": job.get("PositionTitle", "Unknown"),
                "agency": job.get("OrganizationName", "Unknown agency"),
                "location": locations[0].get("LocationName") if locations else "Washington, DC",
                "published": job.get("PublicationStartDate"),
                "url": job.get("PositionURI"),
            })
        if not jobs:
            raise ValueError("no usajobs data")
        return {"jobs": jobs, "trigger_hint": "New relevant posting → Capture Management SOP", "source": "USAJOBS"}
    except Exception:
        return _demo_usajobs()


async def _fetch_newsapi_business_india() -> dict:
    if not settings.NEWSAPI_KEY:
        return _demo_newsapi()
    try:
        data = await http_get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "in", "category": "business", "apiKey": settings.NEWSAPI_KEY},
            headers=_ua("newsapi-business-india"),
        )
        articles = []
        for article in data.get("articles", [])[:5]:
            articles.append({
                "title": article.get("title", "Untitled"),
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "description": article.get("description"),
            })
        if not articles:
            raise ValueError("no newsapi articles")
        return {"articles": articles, "trigger_hint": "Client name appears with negative sentiment keywords → Crisis Comms SOP", "source": "NewsAPI"}
    except Exception:
        return _demo_newsapi()
