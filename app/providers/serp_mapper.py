from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from app.schemas.api.contracts import (
    ExternalAttractionCandidate,
    ExternalEventCandidate,
    ExternalHotelCandidate,
    ExternalRestaurantCandidate,
    ExternalSearchResult,
    ExternalTransportOption,
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "item"


def _category_for(topic: str, raw: dict[str, Any]) -> str:
    content = " ".join(
        [
            topic,
            raw.get("title", ""),
            raw.get("snippet", ""),
            raw.get("type", ""),
        ]
    ).lower()
    if any(token in content for token in ("hotel", "stay", "lodging")):
        return "hotel"
    if any(token in content for token in ("restaurant", "food", "dining", "cafe", "bar")):
        return "restaurant"
    if any(token in content for token in ("event", "festival", "concert", "show", "ticket")):
        return "event"
    if any(token in content for token in ("transport", "transit", "airport", "train", "bus")):
        return "transport"
    return "attraction"


def _tags(raw: dict[str, Any], destination: str, topic: str) -> list[str]:
    tags = [destination.lower(), topic.lower()]
    for candidate in [raw.get("title", ""), raw.get("snippet", "")]:
        tags.extend(token for token in re.findall(r"[a-zA-Z0-9]+", candidate.lower())[:6] if len(token) > 2)
    return list(dict.fromkeys(tag for tag in tags if tag))


def _confidence(raw: dict[str, Any]) -> float | None:
    for key in ("rating", "overall_rating", "stars"):
        value = raw.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def normalize_serp_results(destination: str, topic: str, raw_results: list[dict[str, Any]]) -> list[ExternalSearchResult]:
    normalized: list[ExternalSearchResult] = []
    now = datetime.now(UTC)
    for index, raw in enumerate(raw_results):
        category = _category_for(topic, raw)
        base = {
            "id": raw.get("position") or raw.get("link") or f"serp-{_slug(destination)}-{_slug(topic)}-{index}",
            "name": raw.get("title") or raw.get("name") or f"{destination} {topic.title()} {index + 1}",
            "destination": destination,
            "category": category,
            "tags": _tags(raw, destination, topic),
            "source_url": raw.get("link") or raw.get("url"),
            "snippet": raw.get("snippet") or raw.get("description"),
            "confidence": _confidence(raw),
        }
        if category == "hotel":
            normalized.append(ExternalHotelCandidate(**base, star_rating=float(raw.get("rating", raw.get("stars", 3.0)) or 3.0)))
        elif category == "restaurant":
            normalized.append(ExternalRestaurantCandidate(**base, rating=float(raw.get("rating", 0.0) or 0.0)))
        elif category == "event":
            normalized.append(
                ExternalEventCandidate(
                    **base,
                    starts_at=now,
                    ends_at=now + timedelta(hours=2),
                    venue=raw.get("venue", destination),
                    estimated_cost=float(raw.get("estimated_cost", 0.0) or 0.0),
                )
            )
        elif category == "transport":
            normalized.append(
                ExternalTransportOption(
                    **base,
                    mode=raw.get("mode", "local-transport"),
                    origin=raw.get("origin", destination),
                    destination=destination,
                    duration_minutes=int(raw.get("duration_minutes", 30) or 30),
                    cost_estimate=float(raw.get("cost_estimate", 0.0) or 0.0),
                )
            )
        else:
            normalized.append(ExternalAttractionCandidate(**base, rating=float(raw.get("rating", 0.0) or 0.0)))
    return normalized