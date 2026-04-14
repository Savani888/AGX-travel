from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.core.config import get_settings
from app.core.errors import AppException, ErrorCode

settings = get_settings()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.3),
    retry=retry_if_exception_type(httpx.TimeoutException),
)
def get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=settings.http_timeout_seconds) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise AppException(
            code=ErrorCode.PROVIDER_TIMEOUT,
            message="Provider request timed out",
            retryable=True,
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise AppException(
            code=ErrorCode.PROVIDER_UNAVAILABLE,
            message="Provider unavailable",
            retryable=True,
            status_code=503,
        ) from exc
