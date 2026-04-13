from sqlalchemy.orm import Session

from app.services.context_monitoring_service import ContextMonitoringService


def run_monitoring_tick(db: Session, itinerary_id: str, destination: str) -> dict:
    service = ContextMonitoringService(db)
    weather = service.weather_signal(destination)
    disruption = service.detect_disruption(itinerary_id, destination, weather)
    return {
        "weather": weather.model_dump(),
        "disruption": disruption.model_dump() if disruption else None,
    }
