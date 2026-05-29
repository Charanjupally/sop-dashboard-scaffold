"""
Shared async HTTP client.

All external API calls go through `http_get()` which provides:
  - Connection pooling (one client for the lifetime of the app)
  - Automatic retries with exponential back-off (via tenacity)
  - 10-second timeout
  - Structured error logging
"""
import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None

# Retry on transient network/server errors only
_RETRY_ON = (
    httpx.TimeoutException,
    httpx.NetworkError,
    httpx.RemoteProtocolError,
)


def _should_retry(exc: BaseException) -> bool:
    if isinstance(exc, _RETRY_ON):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return status_code == 429 or 500 <= status_code < 600
    return False


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
    return _client


async def close_http_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()


@retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def http_get(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
) -> Any:
    """
    GET request → parsed JSON.
    Retries up to 3× on network/timeout errors (not on 4xx/5xx).
    Raises httpx.HTTPStatusError on 4xx/5xx after retries are exhausted.
    """
    client = _get_client()
    response = await client.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()
