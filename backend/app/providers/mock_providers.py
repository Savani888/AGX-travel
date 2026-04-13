from datetime import UTC, datetime, timedelta
from random import randint
from typing import Any

from app.providers.interfaces import (
    EventProvider,
    HotelProvider,
    MapsProvider,
    RestaurantProvider,
    TransportProvider,
    WeatherProvider,
)


class MockWeatherProvider(WeatherProvider):
    def weather(self, destination: str) -> dict[str, Any]:
        return {
            "destination": destination,
            "temperature_c": 22,
            "conditions": "clear",
            "rain_probability": 0.1,
        }


class MockMapsProvider(MapsProvider):
    def route(self, origin: str, destination: str) -> dict[str, Any]:
        return {"origin": origin, "destination": destination, "duration_minutes": randint(10, 45)}


class MockHotelProvider(HotelProvider):
    def book_hotel(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "confirmed", "external_reference": f"HOTEL-{randint(1000, 9999)}", "payload": payload}


class MockTransportProvider(TransportProvider):
    def book_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "confirmed",
            "external_reference": f"TRANS-{randint(1000, 9999)}",
            "departure": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
            "payload": payload,
        }


class MockRestaurantProvider(RestaurantProvider):
    def book_restaurant(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "confirmed", "external_reference": f"REST-{randint(1000, 9999)}", "payload": payload}


class MockEventProvider(EventProvider):
    def book_event_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "confirmed", "external_reference": f"TIX-{randint(1000, 9999)}", "payload": payload}
