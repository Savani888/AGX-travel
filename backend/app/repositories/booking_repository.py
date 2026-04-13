from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def get(self, booking_id: str) -> Booking | None:
        return self.db.scalar(select(Booking).where(Booking.id == booking_id))

    def delete(self, booking: Booking) -> None:
        self.db.delete(booking)
        self.db.commit()

    def find_by_idempotency(
        self,
        user_id: str,
        booking_type: str,
        provider: str,
        idempotency_key: str,
    ) -> Booking | None:
        rows = list(
            self.db.scalars(
                select(Booking).where(
                    Booking.user_id == user_id,
                    Booking.booking_type == booking_type,
                    Booking.provider == provider,
                )
            )
        )
        for row in rows:
            if (row.request_payload or {}).get("idempotency_key") == idempotency_key:
                return row
        return None
