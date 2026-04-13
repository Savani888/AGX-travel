from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Register models for metadata discovery.
from app.models import booking, context, explanation, feedback, itinerary, user  # noqa: E402,F401
