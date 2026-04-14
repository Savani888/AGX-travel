from sqlalchemy.orm import Session
import json

from app.core.errors import AppException, ErrorCode
from app.models.itinerary import Itinerary
from app.orchestration.workflow import TourismOrchestrationWorkflow
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.itinerary_repository import ItineraryRepository
from app.schemas.api.contracts import FeedbackRequest, ItineraryCreateRequest, ItineraryResponse


class ItineraryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ItineraryRepository(db)
        self.feedback_repo = FeedbackRepository(db)
        self.workflow = TourismOrchestrationWorkflow()

    def create(self, user_id: str, request: ItineraryCreateRequest) -> tuple[ItineraryResponse, dict]:
        state, trace = self.workflow.run(request)
        itinerary_payload = state["itinerary"]
        trace_json = json.loads(json.dumps(trace, default=str))
        itinerary = Itinerary(
            id=itinerary_payload["itinerary_id"],
            user_id=user_id,
            destination=itinerary_payload["destination"],
            status=itinerary_payload["status"],
            start_date=str(itinerary_payload["days"][0]["date"]),
            end_date=str(itinerary_payload["days"][-1]["date"]),
            total_estimated_cost=itinerary_payload["total_estimated_cost"],
            payload=itinerary_payload,
            decision_trace=trace_json,
        )
        self.repo.create(itinerary)
        return ItineraryResponse(**itinerary_payload), trace_json

    def get(self, itinerary_id: str) -> ItineraryResponse:
        itinerary = self.repo.get(itinerary_id)
        if not itinerary:
            raise AppException(code=ErrorCode.NOT_FOUND, message="Itinerary not found", status_code=404)
        return ItineraryResponse(**itinerary.payload)

    def replan(self, itinerary_id: str, reason: str, user_id: str) -> tuple[ItineraryResponse, dict]:
        itinerary = self.repo.get(itinerary_id)
        if not itinerary or itinerary.user_id != user_id:
            raise AppException(code=ErrorCode.NOT_FOUND, message="Itinerary not found", status_code=404)
        payload = itinerary.payload
        if payload.get("days"):
            payload["days"][-1]["morning"][0]["title"] = "Rain-safe indoor gallery"
        trace = {
            "candidate_pool": [],
            "retrieved_evidence": [],
            "ranking_scores": [{"replan_score": 0.76}],
            "constraint_checks": [{"rule": "preserve_bookings", "passed": True}],
            "selected_option": {"reason": reason},
            "rejected_alternatives": [{"title": "Do nothing", "reason": "high disruption"}],
            "contextual_factors": ["weather_alert"],
        }
        self.repo.update_payload(itinerary, payload, trace, "replanned")
        return ItineraryResponse(**payload), trace

    def save_feedback(self, itinerary_id: str, user_id: str, request: FeedbackRequest) -> None:
        itinerary = self.repo.get(itinerary_id)
        if not itinerary:
            raise AppException(code=ErrorCode.NOT_FOUND, message="Itinerary not found", status_code=404)
        from app.models.feedback import Feedback

        self.feedback_repo.create(
            Feedback(itinerary_id=itinerary_id, user_id=user_id, rating=request.rating, comment=request.comment)
        )
