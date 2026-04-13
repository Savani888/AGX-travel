from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.explanation import ExplanationTraceRecord


class ExplanationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, row: ExplanationTraceRecord) -> ExplanationTraceRecord:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_by_itinerary(self, itinerary_id: str) -> list[ExplanationTraceRecord]:
        return list(
            self.db.scalars(select(ExplanationTraceRecord).where(ExplanationTraceRecord.itinerary_id == itinerary_id))
        )
