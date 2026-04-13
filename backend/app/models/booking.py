import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    itinerary_id: Mapped[str] = mapped_column(String(36), ForeignKey("itineraries.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    booking_type: Mapped[str] = mapped_column(String(50))
    provider: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    external_reference: Mapped[str] = mapped_column(String(255), default="")
    request_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
