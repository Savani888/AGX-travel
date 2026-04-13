from fastapi import APIRouter

from app.api.v1.routers import auth, bookings, context, intent, itineraries, knowledge, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(intent.router, prefix="/intent", tags=["intent"])
api_router.include_router(itineraries.router, prefix="/itineraries", tags=["itineraries"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(context.router, prefix="/context", tags=["context"])
