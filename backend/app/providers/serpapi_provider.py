import asyncio
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import AppException, ErrorCode
from app.providers.interfaces import SearchProvider

logger = logging.getLogger(__name__)


class SerpAPIProvider(SearchProvider):
    endpoint = "https://serpapi.com/search.json"

    def __init__(self, api_key: str | None = None, enabled: bool | None = None, timeout_seconds: int | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.serp_api_key
        self.enabled = settings.serp_enabled if enabled is None else enabled
        self.timeout_seconds = settings.http_timeout_seconds if timeout_seconds is None else timeout_seconds

    async def _search_async(self, query: str, destination: str) -> list[dict[str, Any]]:
        if not self.enabled or not self.api_key:
            return []

        params = {"q": f"{destination} {query} tourism", "api_key": self.api_key, "engine": "google", "num": 10}
        timeout = httpx.Timeout(self.timeout_seconds)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(self.endpoint, params=params)
        except httpx.TimeoutException as exc:
            raise AppException(
                code=ErrorCode.PROVIDER_TIMEOUT,
                message="SerpAPI request timed out",
                details={"provider": "serpapi"},
                retryable=True,
                status_code=504,
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                code=ErrorCode.PROVIDER_UNAVAILABLE,
                message="SerpAPI unavailable",
                details={"provider": "serpapi"},
                retryable=True,
                status_code=503,
            ) from exc

        if response.status_code in {401, 403}:
            raise AppException(
                code=ErrorCode.PROVIDER_UNAVAILABLE,
                message="SerpAPI rejected the API key",
                details={"provider": "serpapi", "status_code": response.status_code},
                retryable=False,
                status_code=502,
            )
        if response.status_code == 429:
            raise AppException(
                code=ErrorCode.PROVIDER_UNAVAILABLE,
                message="SerpAPI rate limit reached",
                details={"provider": "serpapi", "status_code": response.status_code},
                retryable=True,
                status_code=503,
            )

        try:
            response.raise_for_status()
            payload = response.json()
        except ValueError as exc:
            raise AppException(
                code=ErrorCode.PROVIDER_UNAVAILABLE,
                message="SerpAPI returned malformed JSON",
                details={"provider": "serpapi"},
                retryable=True,
                status_code=502,
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                code=ErrorCode.PROVIDER_UNAVAILABLE,
                message="SerpAPI returned an error response",
                details={"provider": "serpapi", "status_code": response.status_code},
                retryable=True,
                status_code=503,
            ) from exc

        organic = payload.get("organic_results")
        if not isinstance(organic, list):
            raise AppException(
                code=ErrorCode.PROVIDER_UNAVAILABLE,
                message="SerpAPI response missing organic results",
                details={"provider": "serpapi"},
                retryable=True,
                status_code=502,
            )

        return [
            {
                "title": row.get("title", ""),
                "snippet": row.get("snippet", ""),
                "url": row.get("link", ""),
                "rating": row.get("rating"),
                "raw": row,
            }
            for row in organic[:8]
        ]

    def _run(self, query: str, destination: str) -> list[dict[str, Any]]:
        return asyncio.run(self._search_async(query, destination))

    def search(self, query: str, destination: str) -> list[dict[str, Any]]:
        return self._run(query, destination)

    def search_destination(self, destination: str, topic: str) -> list[dict[str, Any]]:
        return self._run(topic, destination)


SerpApiSearchProvider = SerpAPIProvider
