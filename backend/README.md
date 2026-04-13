# AGX Tourism Engine Backend

Production-style FastAPI backend for AGX (Agentic Explainable AI) smart tourism planning.

## Stack

- FastAPI (API)
- Pydantic v2 (contracts)
- SQLAlchemy 2.0 + Alembic (ORM + migrations)
- PostgreSQL (persistence)
- Redis (cache, ephemeral session context, booking idempotency)
- httpx + tenacity (provider communication with timeout/retry)
- LangGraph (stateful multi-agent orchestration graph)

## Architecture

```text
app/
	api/v1/routers/         # API layer: validation/auth/delegation only
	services/               # Business logic services
	repositories/           # Persistence adapters
	providers/              # External tool/API adapters (SerpAPI + mock providers)
	orchestration/          # Stateful multi-agent workflow graph
	rag/                    # Vector retrieval layer
	knowledge_graph/        # Relational reasoning graph
	xai/                    # Explainability interfaces
	monitoring/             # Context monitoring hooks
	schemas/api/            # Public request/response contracts
	schemas/internal/       # Internal DTOs for orchestration/services
	models/                 # SQLAlchemy persistence models
	db/                     # Engine/session/base
	core/                   # Config, security, middleware, errors
	utils/                  # Utility helpers
```

## Service Boundaries

- API Routers: auth, input validation, response shaping, delegation.
- Services: domain logic (intent extraction, planning, replanning, explainability, context monitoring, tool execution).
- Repositories: only persistence concerns.
- Providers: third-party wrappers with resilience and stable interfaces.
- Orchestration: coordinates multiple steps/models/tools over typed shared state.
- Schemas: explicit external and internal contracts.

## Multi-Agent Orchestration Flow

LangGraph workflow in `app/orchestration/workflow.py` executes:

1. User input
2. Intent extraction
3. RAG retrieval
4. Candidate scoring
5. Itinerary planning
6. Constraint validation
7. Explanation trace persistence
8. Optional booking execution
9. Context monitoring and disruption detection
10. Partial replanning
11. Updated explanation

## API Endpoints (`/v1`)

### Auth

- `POST /v1/auth/register`
- `POST /v1/auth/login`

### User

- `GET /v1/users/me`
- `PUT /v1/users/me/preferences`

### Intent

- `POST /v1/intent/extract`

### Itinerary

- `POST /v1/itineraries`
- `GET /v1/itineraries/{itinerary_id}`
- `POST /v1/itineraries/{itinerary_id}/replan`
- `GET /v1/itineraries/{itinerary_id}/explanations`
- `GET /v1/itineraries/{itinerary_id}/alternatives`
- `POST /v1/itineraries/{itinerary_id}/feedback`

### Knowledge

- `GET /v1/knowledge/search`
- `GET /v1/knowledge/attractions`
- `GET /v1/knowledge/hotels`
- `GET /v1/knowledge/restaurants`
- `GET /v1/knowledge/events`
- `GET /v1/knowledge/transport`

### Booking

- `POST /v1/bookings/hotels`
- `POST /v1/bookings/transport`
- `POST /v1/bookings/tickets`
- `POST /v1/bookings/restaurants`
- `GET /v1/bookings/{booking_id}`
- `DELETE /v1/bookings/{booking_id}`

### Context

- `GET /v1/context/weather/{destination}`
- `GET /v1/context/traffic`
- `GET /v1/context/crowd/{attraction_id}`
- `GET /v1/context/disruptions/{destination}`
- `POST /v1/context/webhooks`

## Public Contracts

Defined in `app/schemas/api/contracts.py`:

- IntentRequest
- TravelerProfile
- TravelerConstraints
- TravelerPreferences
- IntentExtractionResult
- KnowledgeSearchRequest
- KnowledgeSearchResponse
- AttractionCandidate
- HotelCandidate
- RestaurantCandidate
- EventCandidate
- TransportOption
- ItineraryCreateRequest
- ItineraryResponse
- ItineraryDay
- ItineraryItem
- RouteSegment
- BookingRequest
- BookingResponse
- BookingStatusResponse
- ContextSignal
- DisruptionEvent
- ReplanRequest
- ReplanResponse
- ExplanationTrace
- AlternativeOption
- ConfidenceScore
- FeedbackRequest
- ErrorResponse

Internal DTOs in `app/schemas/internal/dtos.py`:

- PlanningInput
- PlanningCandidateSet
- ValidationReport
- DecisionTrace

## Error Handling

Global handlers return unified shape:

```json
{
	"error": {
		"code": "VALIDATION_ERROR",
		"message": "...",
		"details": {},
		"retryable": false,
		"trace_id": "..."
	}
}
```

Error categories include:

- VALIDATION_ERROR
- AUTH_ERROR
- FORBIDDEN
- NOT_FOUND
- RAG_NO_RESULTS
- PLANNING_CONSTRAINT_FAILURE
- ITINERARY_GENERATION_FAILED
- PROVIDER_TIMEOUT
- PROVIDER_UNAVAILABLE
- BOOKING_FAILED
- BOOKING_CONFLICT
- REPLAN_FAILED
- CONTEXT_SOURCE_ERROR
- INTERNAL_ERROR

## Run

1. Copy env file:
	 - `cp .env.example .env`
2. Start services:
	 - `docker compose up --build`
3. Run migrations:
	 - `alembic upgrade head`
4. API:
	 - `http://localhost:8000/docs`

Port note:

- Docker Compose exposes the API on port 8000.
- Port 8001 is optional and only used if you start uvicorn manually with a different port.
- Example manual run from this folder:
	- `uvicorn app.main:app --host 127.0.0.1 --port 8001`

## Security And Safe Commit Guide

- Never commit `.env` or real API keys.
- Keep secrets only in runtime environment variables or an untracked local `.env` file.
- Use `.env.example` for placeholders only.
- Local SQLite files such as `agx.db`, `serp_manual.db`, and `test_agx.db` are local artifacts and should stay untracked.

Recommended pre-commit checks:

1. Confirm there are no staged secrets:
	- `git diff --staged | grep -E "API_KEY|SECRET|TOKEN|PASSWORD"`
2. Confirm `.env` is not staged:
	- `git status --short | grep -E "\.env$"`
3. Review staged files before commit:
	- `git status --short`

## SerpAPI Fallback Setup

The knowledge service uses local RAG data first, then falls back to SerpAPI only when local results are missing or weak.

Environment variables:

- `SERP_API_KEY`: preferred SerpAPI key variable.
- `SERPAPI_API_KEY`: backward-compatible alias.
- `SERP_ENABLED`: enables live fallback (`true` or `false`).
- `SERP_FALLBACK_MIN_RESULTS`: minimum local result count before fallback is considered.
- `SERP_FALLBACK_CONFIDENCE_THRESHOLD`: minimum local confidence before fallback is considered.

Suggested runtime values:

- `SERP_ENABLED=true`
- `SERP_FALLBACK_MIN_RESULTS=3`
- `SERP_FALLBACK_CONFIDENCE_THRESHOLD=0.6`

Live verification checklist:

1. Start API with Serp fallback enabled.
2. Query a known local destination, for example `Kyoto + temples`.
3. Query a likely-missing destination, for example `Reykjavik + northern lights`.
4. Repeat the same missing-destination query to confirm cache reuse.
5. Temporarily use an invalid key to verify structured provider error handling.

Expected behavior:

- Local-hit query returns `source=local_rag`, `source_type=retrieval`, `provider=vector_store`.
- Fallback query returns `source=serpapi`, `source_type=live_search`, `provider=serpapi`, plus `source_url`, `snippet`, `destination`, `confidence`.
- Repeated fallback query logs a cache hit.
- Invalid key returns structured JSON error with provider details, not a raw traceback.

## Evaluation

- Sample scenarios: `data/scenarios/traveler_scenarios.json`
- Knowledge seed: `data/scenarios/knowledge_base.json`
- Run metric utility:
	- `python scripts/evaluate.py`