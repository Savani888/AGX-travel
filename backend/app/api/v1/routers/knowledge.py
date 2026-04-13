from fastapi import APIRouter, Query

from app.schemas.api.contracts import KnowledgeSearchRequest, KnowledgeSearchResponse
from app.services.knowledge_retrieval_service import KnowledgeRetrievalService

router = APIRouter()


@router.get("/search", response_model=KnowledgeSearchResponse)
def search(destination: str, query: str = Query(..., min_length=2)):
    req = KnowledgeSearchRequest(destination=destination, query=query, filters={})
    return KnowledgeRetrievalService().search(req)


@router.get("/attractions", response_model=KnowledgeSearchResponse)
def attractions(destination: str):
    return KnowledgeRetrievalService().search(
        KnowledgeSearchRequest(destination=destination, query="attractions", filters={"category": "attraction"})
    )


@router.get("/hotels", response_model=KnowledgeSearchResponse)
def hotels(destination: str):
    return KnowledgeRetrievalService().search(
        KnowledgeSearchRequest(destination=destination, query="hotels", filters={"category": "hotel"})
    )


@router.get("/restaurants", response_model=KnowledgeSearchResponse)
def restaurants(destination: str):
    return KnowledgeRetrievalService().search(
        KnowledgeSearchRequest(destination=destination, query="restaurants", filters={"category": "restaurant"})
    )


@router.get("/events", response_model=KnowledgeSearchResponse)
def events(destination: str):
    return KnowledgeRetrievalService().search(
        KnowledgeSearchRequest(destination=destination, query="events", filters={"category": "event"})
    )


@router.get("/transport", response_model=KnowledgeSearchResponse)
def transport(destination: str):
    return KnowledgeRetrievalService().search(
        KnowledgeSearchRequest(destination=destination, query="transport", filters={"category": "transport"})
    )
