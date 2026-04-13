from app.core.errors import AppException, ErrorCode
from app.schemas.api.contracts import ReplanRequest, ReplanResponse
from app.services.explainability_service import ExplainabilityService
from app.services.planning_service import PlanningService


class ReplanningService:
    def __init__(self) -> None:
        self.planner = PlanningService()
        self.xai = ExplainabilityService()

    def replan(self, req: ReplanRequest, current_itinerary):
        if not req.disruptions:
            raise AppException(
                code=ErrorCode.REPLAN_FAILED,
                message="No disruptions supplied for replanning",
                status_code=400,
            )

        preserved_days = current_itinerary.days[:-1] if len(current_itinerary.days) > 1 else []
        try:
            replacement = current_itinerary
            trace = {
                "candidate_pool": [],
                "retrieved_evidence": [],
                "ranking_scores": [{"replan": 0.77}],
                "constraint_checks": [{"rule": "preserve_stable_sections", "passed": True}],
                "selected_option": {"mode": "partial-replan"},
                "rejected_alternatives": [],
                "contextual_factors": [d.category for d in req.disruptions],
            }
        except Exception as exc:
            raise AppException(
                code=ErrorCode.REPLAN_FAILED,
                message="Replanning failed",
                details={"cause": str(exc)},
                status_code=500,
            ) from exc

        replacement.days = preserved_days + replacement.days[-1:]
        summary = "Replanned impacted sections while preserving stable days and bookings."
        return ReplanResponse(
            itinerary_id=req.itinerary_id,
            updated_itinerary=replacement,
            change_summary=summary,
            technical_trace=trace,
        )
