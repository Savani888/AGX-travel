from types import SimpleNamespace

from app.core.errors import AppException, ErrorCode
from app.providers.serp_mapper import normalize_serp_results
from app.providers.serpapi_provider import SerpAPIProvider
from app.services.knowledge_retrieval_service import KnowledgeRetrievalService
from app.rag.vector_store import TourismVectorStore


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl_seconds, value):
        self.store[key] = value
        return True


def _serp_settings():
    return SimpleNamespace(
        serp_enabled=True,
        serp_api_key="test-key",
        serp_fallback_min_results=3,
        serp_fallback_confidence_threshold=0.6,
    )


def test_normalized_response_matches_contract():
    normalized = normalize_serp_results(
        "Kyoto",
        "temples",
        [
            {
                "title": "Kiyomizu-dera",
                "snippet": "Historic temple in Kyoto",
                "link": "https://example.com/kiyomizu",
                "rating": 4.8,
            }
        ],
    )

    assert len(normalized) == 1
    item = normalized[0]
    assert item.name == "Kiyomizu-dera"
    assert item.destination == "Kyoto"
    assert item.category == "attraction"
    assert item.source == "serpapi"
    assert item.source_type == "live_search"
    assert item.provider == "serpapi"
    assert item.source_url == "https://example.com/kiyomizu"
    assert item.snippet == "Historic temple in Kyoto"
    assert item.rating == 4.8


def test_fallback_triggers_when_local_results_are_empty(client, monkeypatch):
    monkeypatch.setattr("app.services.knowledge_retrieval_service.get_settings", _serp_settings)
    monkeypatch.setattr(TourismVectorStore, "query", lambda self, destination, text, k=20: [])
    monkeypatch.setattr(
        SerpAPIProvider,
        "search_destination",
        lambda self, destination, topic: [
            {
                "title": "Kinkaku-ji",
                "snippet": "Golden Pavilion in Kyoto",
                "link": "https://example.com/kinkakuji",
                "rating": 4.9,
            }
        ],
    )

    res = client.get("/v1/knowledge/search?destination=Kyoto&query=temples")

    assert res.status_code == 200
    body = res.json()
    assert body["attractions"]
    attraction = body["attractions"][0]
    assert attraction["destination"] == "Kyoto"
    assert attraction["source"] == "serpapi"
    assert attraction["source_type"] == "live_search"
    assert attraction["provider"] == "serpapi"
    assert attraction["source_url"] == "https://example.com/kinkakuji"


def test_fallback_does_not_trigger_when_local_results_are_sufficient(client, monkeypatch):
    monkeypatch.setattr("app.services.knowledge_retrieval_service.get_settings", _serp_settings)
    monkeypatch.setattr(
        TourismVectorStore,
        "query",
        lambda self, destination, text, k=20: [
            {
                "id": "local-1",
                "destination": "Kyoto",
                "category": "attraction",
                "name": "Kyoto Temple Walk",
                "tags": ["kyoto", "temples"],
            },
            {
                "id": "local-2",
                "destination": "Kyoto",
                "category": "hotel",
                "name": "Kyoto Boutique Stay",
                "tags": ["kyoto", "stay"],
            },
            {
                "id": "local-3",
                "destination": "Kyoto",
                "category": "restaurant",
                "name": "Kyoto Local Kitchen",
                "tags": ["kyoto", "food"],
            },
        ],
    )
    provider_calls = []

    def fail_if_called(self, destination, topic):
        provider_calls.append((destination, topic))
        raise AssertionError("SerpAPI fallback should not be triggered")

    monkeypatch.setattr(SerpAPIProvider, "search_destination", fail_if_called)

    res = client.get("/v1/knowledge/search?destination=Kyoto&query=Kyoto%20temples%20food")

    assert res.status_code == 200
    assert provider_calls == []
    assert all(item["source"] == "local_rag" for item in res.json()["attractions"])


def test_provider_failure_is_handled_safely(client, monkeypatch):
    monkeypatch.setattr("app.services.knowledge_retrieval_service.get_settings", _serp_settings)
    monkeypatch.setattr(
        TourismVectorStore,
        "query",
        lambda self, destination, text, k=20: [
            {
                "id": "local-1",
                "destination": "Kyoto",
                "category": "attraction",
                "name": "Local Kyoto Temple",
                "tags": ["kyoto", "temple"],
            }
        ],
    )

    def raise_provider_error(self, destination, topic):
        raise AppException(
            code=ErrorCode.PROVIDER_UNAVAILABLE,
            message="SerpAPI unavailable",
            retryable=True,
            status_code=503,
        )

    monkeypatch.setattr(SerpAPIProvider, "search_destination", raise_provider_error)

    res = client.get("/v1/knowledge/search?destination=Kyoto&query=temples")

    assert res.status_code == 200
    assert res.json()["attractions"][0]["name"] == "Local Kyoto Temple"


def test_cached_fallback_avoids_duplicate_provider_calls(client, monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr("app.core.cache.redis_client", fake_redis)
    monkeypatch.setattr("app.services.knowledge_retrieval_service.get_settings", _serp_settings)
    monkeypatch.setattr(TourismVectorStore, "query", lambda self, destination, text, k=20: [])

    call_count = {"value": 0}

    def provider_results(self, destination, topic):
        call_count["value"] += 1
        return [
            {
                "title": "Arashiyama Bamboo Grove",
                "snippet": "Popular Kyoto attraction",
                "link": "https://example.com/arashiyama",
                "rating": 4.7,
            }
        ]

    monkeypatch.setattr(SerpAPIProvider, "search_destination", provider_results)

    first = client.get("/v1/knowledge/search?destination=Kyoto&query=bamboo%20grove")
    second = client.get("/v1/knowledge/search?destination=Kyoto&query=bamboo%20grove")

    assert first.status_code == 200
    assert second.status_code == 200
    assert call_count["value"] == 1
    assert second.json()["attractions"][0]["source"] == "serpapi"