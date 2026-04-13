from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.itinerary import Itinerary


class ItineraryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, itinerary: Itinerary) -> Itinerary:
        self.db.add(itinerary)
        self.db.commit()
        self.db.refresh(itinerary)
        return itinerary

    def get(self, itinerary_id: str) -> Itinerary | None:
        return self.db.scalar(select(Itinerary).where(Itinerary.id == itinerary_id))

    def update_payload(self, itinerary: Itinerary, payload: dict, trace: dict, status: str) -> Itinerary:
        itinerary.payload = payload
        itinerary.decision_trace = trace
        itinerary.status = status
        self.db.commit()
        self.db.refresh(itinerary)
        return itinerary
