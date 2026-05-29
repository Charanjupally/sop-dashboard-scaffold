from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret"
    FRONTEND_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sop:sop@localhost:5432/sopdb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── External API Keys ──────────────────────────────
    COINGECKO_API_KEY: str = ""
    ALPHA_VANTAGE_KEY: str = ""
    FRED_API_KEY: str = ""
    AQICN_TOKEN: str = ""
    SEC_USER_AGENT: str = "SOP-Dashboard/1.0 ops@example.com"
    NEWSAPI_KEY: str = ""
    USAJOBS_KEY: str = ""

    NOTION_TOKEN: str = ""
    NOTION_DB_SOP: str = ""
    NOTION_DB_ACTIONS: str = ""

    AIRTABLE_TOKEN: str = ""
    AIRTABLE_BASE_ID: str = ""
    AIRTABLE_TABLE_SOP: str = "SOP Registry"

    CLOCKIFY_API_KEY: str = ""
    CLOCKIFY_WORKSPACE_ID: str = ""

    TRELLO_API_KEY: str = ""
    TRELLO_TOKEN: str = ""
    TRELLO_BOARD_ID: str = ""
    TRELLO_LIST_URGENT: str = ""

    # ── Trigger Thresholds ────────────────────────────
    TRIGGER_BTC_DROP_PCT: float = 5.0
    TRIGGER_ETH_DROP_PCT: float = 8.0
    TRIGGER_FX_MOVE_PCT: float = 2.0
    TRIGGER_CPI_MOM_PCT: float = 0.3
    TRIGGER_AQI_WARN: int = 150
    TRIGGER_AQI_CRITICAL: int = 200
    TRIGGER_UTILIZATION_PCT: float = 90.0
    TRIGGER_SOP_STALE_DAYS: int = 180


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
