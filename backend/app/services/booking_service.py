from sqlalchemy.orm import Session

from app.core.cache import acquire_idempotency_key
from app.core.errors import AppException, ErrorCode
from app.models.booking import Booking
from app.providers.mock_providers import (
    MockEventProvider,
    MockHotelProvider,
    MockRestaurantProvider,
    MockTransportProvider,
)
from app.repositories.booking_repository import BookingRepository
from app.schemas.api.contracts import BookingRequest, BookingResponse, BookingStatusResponse


class BookingToolExecutionService:
    def __init__(self, db: Session):
        self.repo = BookingRepository(db)
        self.hotel_provider = MockHotelProvider()
        self.transport_provider = MockTransportProvider()
        self.restaurant_provider = MockRestaurantProvider()
        self.event_provider = MockEventProvider()
    def execute(self, booking_type: str, req: BookingRequest, user_id: str) -> BookingResponse:
        existing = self.repo.find_by_idempotency(
            user_id=user_id,
            booking_type=booking_type,
            provider=req.provider,
            idempotency_key=req.idempotency_key,
        )
        if existing:
            return BookingResponse(
                booking_id=existing.id,
                status=existing.status,
                provider=existing.provider,
                external_reference=existing.external_reference,
            )

        if not acquire_idempotency_key(req.idempotency_key):
            existing = self.repo.find_by_idempotency(
                user_id=user_id,
                booking_type=booking_type,
                provider=req.provider,
                idempotency_key=req.idempotency_key,
            )
            if existing:
                return BookingResponse(
                    booking_id=existing.id,
                    status=existing.status,
                    provider=existing.provider,
                    external_reference=existing.external_reference,
                )
            raise AppException(code=ErrorCode.BOOKING_CONFLICT, message="Duplicate booking request", status_code=409)

        if booking_type == "hotels":
            provider_result = self.hotel_provider.book_hotel(req.payload)
        elif booking_type == "transport":
            provider_result = self.transport_provider.book_transport(req.payload)
        elif booking_type == "restaurants":
            provider_result = self.restaurant_provider.book_restaurant(req.payload)
        else:
            provider_result = self.event_provider.book_event_ticket(req.payload)

        if provider_result.get("status") != "confirmed":
            raise AppException(
                code=ErrorCode.BOOKING_FAILED,
                message="Provider failed to confirm booking",
                status_code=502,
            )

        booking = Booking(
            itinerary_id=req.itinerary_id,
            user_id=user_id,
            booking_type=booking_type,
            provider=req.provider,
            status="confirmed",
            external_reference=provider_result.get("external_reference", ""),
            request_payload=req.model_dump(),
            response_payload=provider_result,
        )
        created = self.repo.create(booking)
        return BookingResponse(
            booking_id=created.id,
            status=created.status,
            provider=created.provider,
            external_reference=created.external_reference,
        )

    def get(self, booking_id: str) -> BookingStatusResponse:
        booking = self.repo.get(booking_id)
        if not booking:
            raise AppException(code=ErrorCode.NOT_FOUND, message="Booking not found", status_code=404)
        return BookingStatusResponse(booking_id=booking.id, status=booking.status, details=booking.response_payload)

    def delete(self, booking_id: str) -> None:
        booking = self.repo.get(booking_id)
        if not booking:
            raise AppException(code=ErrorCode.NOT_FOUND, message="Booking not found", status_code=404)
        self.repo.delete(booking)
