from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_ERROR = "AUTH_ERROR"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    RAG_NO_RESULTS = "RAG_NO_RESULTS"
    PLANNING_CONSTRAINT_FAILURE = "PLANNING_CONSTRAINT_FAILURE"
    ITINERARY_GENERATION_FAILED = "ITINERARY_GENERATION_FAILED"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    BOOKING_FAILED = "BOOKING_FAILED"
    BOOKING_CONFLICT = "BOOKING_CONFLICT"
    REPLAN_FAILED = "REPLAN_FAILED"
    CONTEXT_SOURCE_ERROR = "CONTEXT_SOURCE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorContent(BaseModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False
    trace_id: str


class ErrorResponse(BaseModel):
    error: ErrorContent


class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
        retryable: bool = False,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.retryable = retryable
        self.status_code = status_code
