from fastapi import APIRouter

from app.schemas.api.contracts import IntentExtractionResult, IntentRequest
from app.services.intent_service import IntentExtractionService

router = APIRouter()


@router.post("/extract", response_model=IntentExtractionResult)
def extract_intent(request: IntentRequest):
    return IntentExtractionService().extract(request)
