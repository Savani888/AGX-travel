from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.context import ContextSnapshot, DisruptionEvent


class ContextRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_snapshot(self, snapshot: ContextSnapshot) -> ContextSnapshot:
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def save_disruption(self, event: DisruptionEvent) -> DisruptionEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_disruptions(self, destination: str) -> list[DisruptionEvent]:
        return list(self.db.scalars(select(DisruptionEvent).where(DisruptionEvent.destination == destination)))
