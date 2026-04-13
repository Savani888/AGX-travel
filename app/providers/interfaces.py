from abc import ABC, abstractmethod
from typing import Any


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, destination: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def search_destination(self, destination: str, topic: str) -> list[dict[str, Any]]:
        return self.search(topic, destination)


class WeatherProvider(ABC):
    @abstractmethod
    def weather(self, destination: str) -> dict[str, Any]:
        raise NotImplementedError


class MapsProvider(ABC):
    @abstractmethod
    def route(self, origin: str, destination: str) -> dict[str, Any]:
        raise NotImplementedError


class HotelProvider(ABC):
    @abstractmethod
    def book_hotel(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class TransportProvider(ABC):
    @abstractmethod
    def book_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class RestaurantProvider(ABC):
    @abstractmethod
    def book_restaurant(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class EventProvider(ABC):
    @abstractmethod
    def book_event_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
