from contextlib import asynccontextmanager

from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import AppException, ErrorCode, ErrorResponse
from app.core.logging import configure_logging
from app.core.middleware import CorrelationIdMiddleware, RequestTimerMiddleware
from app.db.base import Base
from app.db.session import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RequestTimerMiddleware)


@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException):
    trace_id = getattr(request.state, "correlation_id", "unknown")
    payload = ErrorResponse(
        error={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "retryable": exc.retryable,
            "trace_id": trace_id,
        }
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "correlation_id", "unknown")
    safe_errors = jsonable_encoder(exc.errors())
    payload = ErrorResponse(
        error={
            "code": ErrorCode.VALIDATION_ERROR,
            "message": "Request validation failed",
            "details": {"errors": safe_errors},
            "retryable": False,
            "trace_id": trace_id,
        }
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, _: Exception):
    trace_id = getattr(request.state, "correlation_id", "unknown")
    payload = ErrorResponse(
        error={
            "code": ErrorCode.INTERNAL_ERROR,
            "message": "Internal server error",
            "details": {},
            "retryable": False,
            "trace_id": trace_id,
        }
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
