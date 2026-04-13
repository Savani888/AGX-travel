from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.context import ContextSnapshot, DisruptionEvent as DisruptionEventModel
from app.providers.mock_providers import MockMapsProvider, MockWeatherProvider
from app.repositories.context_repository import ContextRepository
from app.schemas.api.contracts import ContextSignal, DisruptionEvent


class ContextMonitoringService:
    def __init__(self, db: Session):
        self.repo = ContextRepository(db)
        self.weather = MockWeatherProvider()
        self.maps = MockMapsProvider()

    def weather_signal(self, destination: str) -> ContextSignal:
        payload = self.weather.weather(destination)
        signal = ContextSignal(
            destination=destination,
            signal_type="weather",
            value=payload,
            severity="high" if payload.get("rain_probability", 0) > 0.7 else "low",
            captured_at=datetime.now(UTC),
        )
        self.repo.save_snapshot(
            ContextSnapshot(
                destination=destination,
                signal_type="weather",
                payload=signal.model_dump(mode="json"),
                severity=signal.severity,
            )
        )
        return signal

    def traffic_signal(self, origin: str, destination: str) -> ContextSignal:
        payload = self.maps.route(origin, destination)
        signal = ContextSignal(
            destination=destination,
            signal_type="traffic",
            value=payload,
            severity="medium" if payload.get("duration_minutes", 0) > 35 else "low",
            captured_at=datetime.now(UTC),
        )
        self.repo.save_snapshot(
            ContextSnapshot(
                destination=destination,
                signal_type="traffic",
                payload=signal.model_dump(mode="json"),
                severity=signal.severity,
            )
        )
        return signal

    def detect_disruption(self, itinerary_id: str, destination: str, signal: ContextSignal) -> DisruptionEvent | None:
        if signal.severity == "low":
            return None
        event = DisruptionEvent(
            destination=destination,
            category=signal.signal_type,
            details=signal.value,
            impact_score="high" if signal.severity == "high" else "medium",
        )
        self.repo.save_disruption(
            DisruptionEventModel(
                itinerary_id=itinerary_id,
                destination=destination,
                category=event.category,
                payload=event.model_dump(mode="json"),
                impact_score=event.impact_score,
            )
        )
        return event

    def list_disruptions(self, destination: str) -> list[DisruptionEvent]:
        rows = self.repo.list_disruptions(destination)
        return [
            DisruptionEvent(
                destination=r.destination,
                category=r.category,
                details=r.payload,
                impact_score=r.impact_score,
            )
            for r in rows
        ]
