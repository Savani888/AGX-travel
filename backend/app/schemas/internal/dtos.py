from typing import Any

from pydantic import BaseModel, Field

from app.schemas.api.contracts import IntentExtractionResult, TravelerProfile


class PlanningInput(BaseModel):
    intent: IntentExtractionResult
    traveler_profile: TravelerProfile | None = None
    weather_context: dict[str, Any] = Field(default_factory=dict)
    traffic_context: dict[str, Any] = Field(default_factory=dict)


class PlanningCandidateSet(BaseModel):
    attractions: list[dict[str, Any]] = Field(default_factory=list)
    hotels: list[dict[str, Any]] = Field(default_factory=list)
    restaurants: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    transport: list[dict[str, Any]] = Field(default_factory=list)


class ValidationReport(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DecisionTrace(BaseModel):
    stage: str
    scores: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[dict[str, Any]] = Field(default_factory=list)
    selected: dict[str, Any] = Field(default_factory=dict)
    rejected: list[dict[str, Any]] = Field(default_factory=list)
