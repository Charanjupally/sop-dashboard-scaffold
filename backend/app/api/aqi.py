"""
/api/aqi — Air quality (AQICN) + weather (Open-Meteo) for office cities
"""
from fastapi import APIRouter
from app.core.cache import cached, TTL_AQI, TTL_WEATHER
from app.core.http import http_get
from app.core.config import settings

router = APIRouter()

CITIES = [
    {"city": "Hyderabad", "lat": 17.385,  "lon": 78.487,  "aqicn_slug": "hyderabad"},
    {"city": "Mumbai",    "lat": 19.076,  "lon": 72.878,  "aqicn_slug": "mumbai"},
    {"city": "Delhi",     "lat": 28.704,  "lon": 77.102,  "aqicn_slug": "delhi"},
    {"city": "Bengaluru", "lat": 12.972,  "lon": 77.594,  "aqicn_slug": "bangalore"},
]


async def _fetch_aqi_city(slug: str) -> int | None:
    try:
        data = await http_get(
            f"https://api.waqi.info/feed/{slug}/",
            params={"token": settings.AQICN_TOKEN},
        )
        if data.get("status") == "ok":
            return int(data["data"]["aqi"])
    except Exception:
        pass
    return None


async def _fetch_weather_city(lat: float, lon: float) -> dict:
    try:
        data = await http_get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
                "forecast_days": 1,
            },
        )
        c = data.get("current", {})
        return {
            "temp_c": c.get("temperature_2m"),
            "humidity": c.get("relative_humidity_2m"),
            "weather_code": c.get("weather_code"),
        }
    except Exception:
        return {}


async def _fetch_all():
    results = []
    for c in CITIES:
        aqi     = await _fetch_aqi_city(c["aqicn_slug"])
        weather = await _fetch_weather_city(c["lat"], c["lon"])
        results.append({
            "city": c["city"],
            "aqi": aqi,
            "temp_c": weather.get("temp_c"),
            "humidity": weather.get("humidity"),
            "weather_code": weather.get("weather_code"),
        })
    return {"cities": results}


@router.get("/")
async def get_aqi():
    return await cached("aqi:all", TTL_AQI, _fetch_all)
