import logging
import re
from typing import Any

from app.core.cache import get_cached_json, set_cached_json
from app.core.config import get_settings
from app.core.errors import AppException, ErrorCode
from app.knowledge_graph.service import TourismKnowledgeGraphService
from app.providers.serp_mapper import normalize_serp_results
from app.providers.serpapi_provider import SerpAPIProvider
from app.rag.vector_store import TourismVectorStore
from app.schemas.api.contracts import (
    AttractionCandidate,
    EventCandidate,
    HotelCandidate,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    RestaurantCandidate,
    TransportOption,
)

logger = logging.getLogger(__name__)


class KnowledgeRetrievalService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.vector = TourismVectorStore()
        self.search_provider = SerpAPIProvider()
        self.kg = TourismKnowledgeGraphService()

    def _query_tokens(self, request: KnowledgeSearchRequest) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", f"{request.destination} {request.query}".lower()))

    def _local_confidence(self, rows: list[dict[str, Any]], request: KnowledgeSearchRequest) -> float:
        if not rows:
            return 0.0
        tokens = self._query_tokens(request)
        if not tokens:
            return 0.0
        top = rows[0]
        haystack = " ".join(
            [top.get("name", ""), " ".join(top.get("tags", [])), top.get("category", ""), top.get("destination", "")]
        ).lower()
        row_tokens = set(re.findall(r"[a-z0-9]+", haystack))
        confidence = len(tokens.intersection(row_tokens)) / len(tokens)
        if top.get("destination", "").lower() == request.destination.lower():
            confidence = min(1.0, confidence + 0.2)
        return confidence

    def _should_use_fallback(self, rows: list[dict[str, Any]], request: KnowledgeSearchRequest) -> bool:
        if not self.settings.serp_enabled or not self.settings.serp_api_key:
            return False
        return len(rows) < self.settings.serp_fallback_min_results or self._local_confidence(rows, request) < self.settings.serp_fallback_confidence_threshold

    def _cache_key(self, destination: str, topic: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", f"{destination}:{topic}".lower()).strip("_")
        return f"serp:{slug}"

    def _local_candidate(self, row: dict[str, Any], confidence: float) -> dict[str, Any]:
        payload = dict(row)
        payload.setdefault("source", "local_rag")
        payload.setdefault("source_type", "retrieval")
        payload.setdefault("provider", "vector_store")
        payload["confidence"] = confidence
        return payload

    def _bucket_local_rows(
        self, rows: list[dict[str, Any]], confidence: float
    ) -> tuple[list[AttractionCandidate], list[HotelCandidate], list[RestaurantCandidate], list[EventCandidate], list[TransportOption]]:
        attractions, hotels, restaurants, events, transport = [], [], [], [], []
        for row in rows:
            payload = self._local_candidate(row, confidence)
            category = row.get("category", "")
            if category == "attraction":
                attractions.append(AttractionCandidate(**payload))
            elif category == "hotel":
                hotels.append(HotelCandidate(**payload))
            elif category == "restaurant":
                restaurants.append(RestaurantCandidate(**payload))
            elif category == "event":
                events.append(EventCandidate(**payload))
            elif category == "transport":
                transport.append(TransportOption(**payload))
        return attractions, hotels, restaurants, events, transport

    def _bucket_external_results(
        self, results: list[dict[str, Any]]
    ) -> tuple[list[AttractionCandidate], list[HotelCandidate], list[RestaurantCandidate], list[EventCandidate], list[TransportOption]]:
        attractions, hotels, restaurants, events, transport = [], [], [], [], []
        for payload in results:
            category = payload.get("category", "")
            if category == "hotel":
                hotels.append(HotelCandidate(**payload))
            elif category == "restaurant":
                restaurants.append(RestaurantCandidate(**payload))
            elif category == "event":
                events.append(EventCandidate(**payload))
            elif category == "transport":
                transport.append(TransportOption(**payload))
            else:
                attractions.append(AttractionCandidate(**payload))
        return attractions, hotels, restaurants, events, transport

    def _merge_category(self, local: list[Any], external: list[Any]) -> list[Any]:
        merged: list[Any] = []
        seen: set[tuple[str, str]] = set()
        for item in [*local, *external]:
            if hasattr(item, "category"):
                key = (getattr(item, "category"), getattr(item, "name", getattr(item, "id", "")))
            else:
                key = (getattr(item, "mode", "transport"), getattr(item, "id", ""))
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

    def search(self, request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
        rows = self.vector.query(request.destination, request.query)
        confidence = self._local_confidence(rows, request)
        logger.info(
            "knowledge search local_result_count=%s confidence=%.2f destination=%s query=%s",
            len(rows),
            confidence,
            request.destination,
            request.query,
        )

        local_buckets = self._bucket_local_rows(rows, confidence)
        if rows:
            self.kg.ingest_entities(rows)
            self.kg.enrich_proximity()

        fallback_results: list[dict[str, Any]] = []
        should_fallback = self._should_use_fallback(rows, request)
        logger.info(
            "knowledge search fallback_triggered=%s min_results=%s threshold=%.2f",
            should_fallback,
            self.settings.serp_fallback_min_results,
            self.settings.serp_fallback_confidence_threshold,
        )

        if should_fallback:
            topic = request.filters.get("category") or request.query
            cache_key = self._cache_key(request.destination, topic)
            cached = get_cached_json(cache_key)
            if isinstance(cached, list):
                fallback_results = cached
                logger.info("knowledge search serpapi_cache_hit key=%s normalized_result_count=%s", cache_key, len(cached))
            else:
                try:
                    raw_results = self.search_provider.search_destination(request.destination, topic)
                    normalized = normalize_serp_results(request.destination, topic, raw_results)
                    fallback_results = [result.model_dump(mode="json") for result in normalized]
                    set_cached_json(cache_key, fallback_results, ttl_seconds=3600)
                    logger.info(
                        "knowledge search serpapi_cache_miss key=%s raw_result_count=%s normalized_result_count=%s",
                        cache_key,
                        len(raw_results),
                        len(fallback_results),
                    )
                except AppException as exc:
                    logger.warning("knowledge search serpapi_failed destination=%s query=%s error=%s", request.destination, topic, exc.message)
                    if not rows:
                        raise

        external_buckets = self._bucket_external_results(fallback_results)
        merged = tuple(self._merge_category(local, external) for local, external in zip(local_buckets, external_buckets, strict=False))
        evidence = [
            *[
                row
                | {
                    "source": "local_rag",
                    "source_type": "retrieval",
                    "provider": "vector_store",
                    "confidence": confidence,
                }
                for row in rows
            ],
            *fallback_results,
        ]

        attractions, hotels, restaurants, events, transport = merged
        if not any((attractions, hotels, restaurants, events, transport)):
            raise AppException(
                code=ErrorCode.RAG_NO_RESULTS,
                message="No tourism knowledge found",
                details={"destination": request.destination, "query": request.query},
                retryable=False,
                status_code=404,
            )

        return KnowledgeSearchResponse(
            destination=request.destination,
            attractions=attractions,
            hotels=hotels,
            restaurants=restaurants,
            events=events,
            transport=transport,
            evidence=evidence,
        )
