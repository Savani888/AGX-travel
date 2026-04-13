from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.api.contracts import (
    AlternativeOption,
    ExplanationTrace,
    FeedbackRequest,
    ItineraryCreateRequest,
    ItineraryResponse,
    ReplanRequest,
    ReplanResponse,
)
from app.services.explainability_service import ExplainabilityService
from app.services.itinerary_service import ItineraryService

router = APIRouter()


@router.post("", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
def create_itinerary(
    request: ItineraryCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    itinerary, trace = ItineraryService(db).create(user.id, request)
    trace_id = ExplainabilityService(db).store(
        itinerary_id=itinerary.itinerary_id,
        summary="Itinerary selected via deterministic constraints + candidate scoring.",
        decision_trace=trace,
        confidence=[{"metric": "overall", "score": 0.84}],
    )
    itinerary.explanation_trace_id = trace_id
    return itinerary


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
def get_itinerary(itinerary_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return ItineraryService(db).get(itinerary_id)


@router.post("/{itinerary_id}/replan", response_model=ReplanResponse)
def replan_itinerary(
    itinerary_id: str,
    request: ReplanRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated, trace = ItineraryService(db).replan(itinerary_id, request.reason, user.id)
    return ReplanResponse(
        itinerary_id=itinerary_id,
        updated_itinerary=updated,
        change_summary="Impacted activities replaced while preserving stable itinerary sections.",
        technical_trace=trace,
    )


@router.get("/{itinerary_id}/explanations", response_model=list[ExplanationTrace])
def list_explanations(itinerary_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return ExplainabilityService(db).list_for_itinerary(itinerary_id)


@router.get("/{itinerary_id}/alternatives", response_model=list[AlternativeOption])
def itinerary_alternatives(itinerary_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    itinerary = ItineraryService(db).get(itinerary_id)
    return itinerary.alternatives


@router.post("/{itinerary_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def feedback(
    itinerary_id: str,
    request: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ItineraryService(db).save_feedback(itinerary_id, user.id, request)
