from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.api.contracts import ContextSignal, DisruptionEvent
from app.services.context_monitoring_service import ContextMonitoringService

router = APIRouter()


@router.get("/weather/{destination}", response_model=ContextSignal)
def weather(destination: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return ContextMonitoringService(db).weather_signal(destination)


@router.get("/traffic", response_model=ContextSignal)
def traffic(origin: str, destination: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return ContextMonitoringService(db).traffic_signal(origin, destination)


@router.get("/crowd/{attraction_id}", response_model=ContextSignal)
def crowd(attraction_id: str, destination: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return ContextSignal(
        destination=destination,
        signal_type="crowd",
        value={"attraction_id": attraction_id, "density": "medium"},
        severity="medium",
        captured_at=datetime.now(UTC),
    )


@router.get("/disruptions/{destination}", response_model=list[DisruptionEvent])
def disruptions(destination: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return ContextMonitoringService(db).list_disruptions(destination)


@router.post("/webhooks")
def webhook(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    _ = db
    return {"received": True, "payload": payload}
