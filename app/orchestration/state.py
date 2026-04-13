from typing import Any, TypedDict

from app.schemas.api.contracts import IntentRequest


class OrchestrationState(TypedDict, total=False):
    raw_intent: IntentRequest
    extracted_intent: dict[str, Any]
    profile: dict[str, Any]
    rag_results: dict[str, Any]
    kg_enrichment: dict[str, Any]
    scored_candidates: dict[str, Any]
    itinerary: dict[str, Any]
    validation: dict[str, Any]
    explanation: dict[str, Any]
    booking: dict[str, Any]
    context: dict[str, Any]
    disruptions: dict[str, Any]
    replan: dict[str, Any]
