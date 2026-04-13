import uuid
from datetime import date, timedelta
from typing import Any

from app.core.errors import AppException, ErrorCode
from app.schemas.api.contracts import (
    AlternativeOption,
    IntentExtractionResult,
    ItineraryCreateRequest,
    ItineraryDay,
    ItineraryItem,
    ItineraryResponse,
    RouteSegment,
)
from app.schemas.internal.dtos import PlanningCandidateSet, PlanningInput, ValidationReport


class PlanningService:
    def deterministic_validate(self, plan: ItineraryResponse, budget: float | None) -> ValidationReport:
        total = sum(day.estimated_day_cost for day in plan.days)
        errors = []
        if budget is not None and total > budget:
            errors.append("Budget exceeded")
        for day in plan.days:
            if not (day.morning or day.afternoon or day.evening):
                errors.append(f"Day {day.day_index} has no activities")
        return ValidationReport(valid=not errors, errors=errors)

    def create(
        self,
        request: ItineraryCreateRequest,
        extracted_intent: IntentExtractionResult,
        candidates: PlanningCandidateSet,
    ) -> tuple[ItineraryResponse, dict[str, Any]]:
        if request.intent.query.strip() == "":
            raise AppException(
                code=ErrorCode.ITINERARY_GENERATION_FAILED,
                message="Cannot generate itinerary for empty intent",
                status_code=400,
            )

        planning_input = PlanningInput(intent=extracted_intent, traveler_profile=request.intent.profile)
        _ = planning_input

        start = date.today()
        duration = extracted_intent.duration_days
        days: list[ItineraryDay] = []
        daily_budget = (extracted_intent.budget / duration) if extracted_intent.budget else 150

        for idx in range(duration):
            morning = [
                ItineraryItem(
                    id=f"itm-{idx}-m1",
                    title="Iconic city walk",
                    category="attraction",
                    start_time="09:00",
                    end_time="11:00",
                    estimated_cost=15,
                    travel_time_minutes=20,
                    reasoning_tags=["open_hours_ok", "walkable", "photo_spot"],
                    fallback_alternatives=["Local museum", "Scenic viewpoint"],
                )
            ]
            afternoon = [
                ItineraryItem(
                    id=f"itm-{idx}-a1",
                    title="Local cuisine lunch",
                    category="restaurant",
                    start_time="13:00",
                    end_time="14:30",
                    estimated_cost=25,
                    travel_time_minutes=15,
                    reasoning_tags=["diet_match", "budget_fit"],
                    fallback_alternatives=["Street food market"],
                )
            ]
            evening = [
                ItineraryItem(
                    id=f"itm-{idx}-e1",
                    title="Culture event",
                    category="event",
                    start_time="18:00",
                    end_time="20:00",
                    estimated_cost=35,
                    travel_time_minutes=25,
                    reasoning_tags=["weather_safe", "high_rating"],
                    fallback_alternatives=["Sunset river cruise"],
                )
            ]
            route_segments = [
                RouteSegment(
                    from_item_id=morning[0].id,
                    to_item_id=afternoon[0].id,
                    mode="metro",
                    travel_minutes=afternoon[0].travel_time_minutes,
                ),
                RouteSegment(
                    from_item_id=afternoon[0].id,
                    to_item_id=evening[0].id,
                    mode="taxi",
                    travel_minutes=evening[0].travel_time_minutes,
                ),
            ]
            day_cost = sum(i.estimated_cost for i in (morning + afternoon + evening))
            if day_cost > daily_budget * 1.4:
                raise AppException(
                    code=ErrorCode.PLANNING_CONSTRAINT_FAILURE,
                    message="Unable to fit day activities into budget",
                    status_code=422,
                )
            days.append(
                ItineraryDay(
                    day_index=idx + 1,
                    date=start + timedelta(days=idx),
                    morning=morning,
                    afternoon=afternoon,
                    evening=evening,
                    route_segments=route_segments,
                    estimated_day_cost=day_cost,
                )
            )

        itinerary_id = str(uuid.uuid4())
        response = ItineraryResponse(
            itinerary_id=itinerary_id,
            destination=extracted_intent.destination,
            status="generated",
            days=days,
            total_estimated_cost=sum(d.estimated_day_cost for d in days),
            alternatives=[
                AlternativeOption(option_id="alt-1", title="Art-first itinerary", score=0.81, reason="Better for cultural interest"),
                AlternativeOption(option_id="alt-2", title="Family relaxed pace", score=0.73, reason="Lower walking load"),
            ],
        )
        report = self.deterministic_validate(response, extracted_intent.budget)
        if not report.valid:
            raise AppException(
                code=ErrorCode.PLANNING_CONSTRAINT_FAILURE,
                message="Constraint checks failed",
                details={"errors": report.errors},
                status_code=422,
            )
        trace = {
            "candidate_pool": candidates.model_dump(),
            "constraint_checks": report.model_dump(),
            "ranking_scores": [{"itinerary": "default", "score": 0.84}],
            "selected_option": {"itinerary_id": itinerary_id},
            "rejected_alternatives": [{"id": "alt-2", "reason": "slightly lower feasibility"}],
            "contextual_factors": ["weather-clear", "traffic-moderate"],
            "retrieved_evidence": [],
        }
        return response, trace
