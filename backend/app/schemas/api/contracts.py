from datetime import date as dt_date
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfidenceScore(BaseModel):
    metric: str
    score: float = Field(ge=0.0, le=1.0)


class TravelerConstraints(BaseModel):
    budget_max: float | None = None
    mobility_constraints: list[str] = Field(default_factory=list)
    accessibility_required: bool = False
    dietary_constraints: list[str] = Field(default_factory=list)


class TravelerPreferences(BaseModel):
    travel_style: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    accommodation_preferences: list[str] = Field(default_factory=list)
    dining_preferences: list[str] = Field(default_factory=list)
    pace: Literal["slow", "balanced", "fast"] = "balanced"


class TravelerProfile(BaseModel):
    user_id: str
    group_size: int = Field(default=1, ge=1)
    season: str | None = None
    preferences: TravelerPreferences = Field(default_factory=TravelerPreferences)
    constraints: TravelerConstraints = Field(default_factory=TravelerConstraints)


class IntentRequest(BaseModel):
    query: str
    profile: TravelerProfile | None = None
    preference_form: dict[str, Any] = Field(default_factory=dict)


class IntentExtractionResult(BaseModel):
    destination: str
    start_date: dt_date | None = None
    end_date: dt_date | None = None
    duration_days: int = Field(default=3, ge=1, le=30)
    budget: float | None = None
    group_size: int = Field(default=1, ge=1)
    travel_style: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    mobility_constraints: list[str] = Field(default_factory=list)
    season: str | None = None
    pace: str = "balanced"
    accommodation_preferences: list[str] = Field(default_factory=list)
    dining_preferences: list[str] = Field(default_factory=list)
    confidence_flags: list[ConfidenceScore] = Field(default_factory=list)


class KnowledgeSearchRequest(BaseModel):
    destination: str
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)


class AttractionCandidate(BaseModel):
    id: str
    name: str
    category: str
    destination: str | None = None
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    cost_band: str = "mid"
    tags: list[str] = Field(default_factory=list)
    coordinates: tuple[float, float] | None = None
    open_hours: dict[str, str] = Field(default_factory=dict)
    source: str = "local_rag"
    source_type: str = "retrieval"
    provider: str = "vector_store"
    source_url: str | None = None
    snippet: str | None = None
    confidence: float | None = None


class HotelCandidate(BaseModel):
    id: str
    name: str
    destination: str | None = None
    star_rating: float = Field(default=3.0, ge=1.0, le=5.0)
    price_per_night: float = Field(default=100.0, ge=0.0)
    tags: list[str] = Field(default_factory=list)
    coordinates: tuple[float, float] | None = None
    source: str = "local_rag"
    source_type: str = "retrieval"
    provider: str = "vector_store"
    source_url: str | None = None
    snippet: str | None = None
    confidence: float | None = None


class RestaurantCandidate(BaseModel):
    id: str
    name: str
    destination: str | None = None
    cuisine: list[str] = Field(default_factory=list)
    price_band: str = "mid"
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    coordinates: tuple[float, float] | None = None
    source: str = "local_rag"
    source_type: str = "retrieval"
    provider: str = "vector_store"
    source_url: str | None = None
    snippet: str | None = None
    confidence: float | None = None


class EventCandidate(BaseModel):
    id: str
    name: str
    destination: str | None = None
    starts_at: datetime
    ends_at: datetime
    venue: str
    ticket_required: bool = False
    estimated_cost: float = 0.0
    source: str = "local_rag"
    source_type: str = "retrieval"
    provider: str = "vector_store"
    source_url: str | None = None
    snippet: str | None = None
    confidence: float | None = None


class TransportOption(BaseModel):
    id: str
    mode: str
    origin: str
    destination: str
    duration_minutes: int
    cost_estimate: float
    source: str = "local_rag"
    source_type: str = "retrieval"
    provider: str = "vector_store"
    source_url: str | None = None
    snippet: str | None = None
    confidence: float | None = None


class ExternalSearchResult(BaseModel):
    destination: str | None = None
    source: str = "serpapi"
    source_type: str = "live_search"
    provider: str = "serpapi"
    source_url: str | None = None
    snippet: str | None = None
    confidence: float | None = None


class ExternalAttractionCandidate(AttractionCandidate):
    source: str = "serpapi"
    source_type: str = "live_search"
    provider: str = "serpapi"


class ExternalHotelCandidate(HotelCandidate):
    source: str = "serpapi"
    source_type: str = "live_search"
    provider: str = "serpapi"


class ExternalRestaurantCandidate(RestaurantCandidate):
    source: str = "serpapi"
    source_type: str = "live_search"
    provider: str = "serpapi"


class ExternalEventCandidate(EventCandidate):
    source: str = "serpapi"
    source_type: str = "live_search"
    provider: str = "serpapi"


class ExternalTransportOption(TransportOption):
    source: str = "serpapi"
    source_type: str = "live_search"
    provider: str = "serpapi"


class KnowledgeSearchResponse(BaseModel):
    destination: str
    attractions: list[AttractionCandidate] = Field(default_factory=list)
    hotels: list[HotelCandidate] = Field(default_factory=list)
    restaurants: list[RestaurantCandidate] = Field(default_factory=list)
    events: list[EventCandidate] = Field(default_factory=list)
    transport: list[TransportOption] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class RouteSegment(BaseModel):
    from_item_id: str
    to_item_id: str
    mode: str
    travel_minutes: int


class ItineraryItem(BaseModel):
    id: str
    title: str
    category: str
    start_time: str
    end_time: str
    estimated_cost: float
    travel_time_minutes: int = 0
    coordinates: tuple[float, float] | None = None
    reasoning_tags: list[str] = Field(default_factory=list)
    fallback_alternatives: list[str] = Field(default_factory=list)


class ItineraryDay(BaseModel):
    day_index: int
    date: dt_date | None = None
    morning: list[ItineraryItem] = Field(default_factory=list)
    afternoon: list[ItineraryItem] = Field(default_factory=list)
    evening: list[ItineraryItem] = Field(default_factory=list)
    route_segments: list[RouteSegment] = Field(default_factory=list)
    estimated_day_cost: float = 0.0


class ItineraryCreateRequest(BaseModel):
    intent: IntentRequest
    enforce_booking_readiness: bool = False


class DecisionTrace(BaseModel):
    candidate_pool: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_evidence: list[dict[str, Any]] = Field(default_factory=list)
    ranking_scores: list[dict[str, Any]] = Field(default_factory=list)
    constraint_checks: list[dict[str, Any]] = Field(default_factory=list)
    selected_option: dict[str, Any] = Field(default_factory=dict)
    rejected_alternatives: list[dict[str, Any]] = Field(default_factory=list)
    contextual_factors: list[str] = Field(default_factory=list)


class ExplanationTrace(BaseModel):
    itinerary_id: str
    summary: str
    confidence: list[ConfidenceScore] = Field(default_factory=list)
    decision_trace: DecisionTrace


class AlternativeOption(BaseModel):
    option_id: str
    title: str
    score: float
    reason: str


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    itinerary_id: str
    destination: str
    status: str
    days: list[ItineraryDay]
    total_estimated_cost: float
    explanation_trace_id: str | None = None
    alternatives: list[AlternativeOption] = Field(default_factory=list)


class BookingRequest(BaseModel):
    itinerary_id: str
    item_id: str
    provider: str
    payload: dict[str, Any]
    idempotency_key: str


class BookingResponse(BaseModel):
    booking_id: str
    status: str
    provider: str
    external_reference: str | None = None


class BookingStatusResponse(BaseModel):
    booking_id: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class ContextSignal(BaseModel):
    destination: str
    signal_type: str
    value: dict[str, Any]
    severity: Literal["low", "medium", "high"] = "low"
    captured_at: datetime


class DisruptionEvent(BaseModel):
    destination: str
    category: str
    details: dict[str, Any] = Field(default_factory=dict)
    impact_score: Literal["low", "medium", "high"] = "medium"


class ReplanRequest(BaseModel):
    itinerary_id: str
    reason: str
    disruptions: list[DisruptionEvent] = Field(default_factory=list)
    preserve_bookings: bool = True


class ReplanResponse(BaseModel):
    itinerary_id: str
    updated_itinerary: ItineraryResponse
    change_summary: str
    technical_trace: DecisionTrace


class FeedbackRequest(BaseModel):
    rating: float = Field(ge=1.0, le=5.0)
    comment: str = ""


class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str | None = None
    name: str | None = None

    @model_validator(mode="after")
    def normalize_names(self):
        if not self.full_name and self.name:
            self.full_name = self.name
        if self.full_name:
            self.full_name = self.full_name.strip()
        if not self.full_name:
            raise ValueError("full_name or name is required")
        return self


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    preferences: dict[str, Any] = Field(default_factory=dict)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False
    trace_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
