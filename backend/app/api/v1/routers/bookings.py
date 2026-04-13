from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.api.contracts import BookingRequest, BookingResponse, BookingStatusResponse
from app.services.booking_service import BookingToolExecutionService

router = APIRouter()


@router.post("/hotels", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def book_hotel(request: BookingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return BookingToolExecutionService(db).execute("hotels", request, user.id)


@router.post("/transport", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def book_transport(request: BookingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return BookingToolExecutionService(db).execute("transport", request, user.id)


@router.post("/tickets", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def book_ticket(request: BookingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return BookingToolExecutionService(db).execute("tickets", request, user.id)


@router.post("/restaurants", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def book_restaurant(request: BookingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return BookingToolExecutionService(db).execute("restaurants", request, user.id)


@router.get("/{booking_id}", response_model=BookingStatusResponse)
def get_booking(booking_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    return BookingToolExecutionService(db).get(booking_id)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    BookingToolExecutionService(db).delete(booking_id)
