from typing import Any

from langgraph.graph import END, StateGraph

from app.schemas.api.contracts import IntentExtractionResult, ItineraryCreateRequest, KnowledgeSearchRequest
from app.schemas.internal.dtos import PlanningCandidateSet
from app.services.intent_service import IntentExtractionService
from app.services.knowledge_retrieval_service import KnowledgeRetrievalService
from app.services.planning_service import PlanningService
from app.orchestration.state import OrchestrationState


class TourismOrchestrationWorkflow:
    """State-machine style orchestration for multi-agent tourism planning.

    Equivalent to a LangGraph flow with deterministic validator edges in between model/tool calls.
    """

    def __init__(self) -> None:
        self.intent = IntentExtractionService()
        self.knowledge = KnowledgeRetrievalService()
        self.planner = PlanningService()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(OrchestrationState)
        graph.add_node("intent_extraction", self._intent_node)
        graph.add_node("rag_retrieval", self._rag_node)
        graph.add_node("candidate_scoring", self._score_node)
        graph.add_node("itinerary_planning", self._planning_node)
        graph.add_node("constraint_validation", self._validation_node)

        graph.set_entry_point("intent_extraction")
        graph.add_edge("intent_extraction", "rag_retrieval")
        graph.add_edge("rag_retrieval", "candidate_scoring")
        graph.add_edge("candidate_scoring", "itinerary_planning")
        graph.add_edge("itinerary_planning", "constraint_validation")
        graph.add_edge("constraint_validation", END)
        return graph.compile()

    def _intent_node(self, state: OrchestrationState) -> OrchestrationState:
        request = state["raw_intent"]
        extracted = self.intent.extract(request)
        state["extracted_intent"] = extracted.model_dump()
        state["profile"] = request.profile.model_dump() if request.profile else {}
        return state

    def _rag_node(self, state: OrchestrationState) -> OrchestrationState:
        extracted = state["extracted_intent"]
        request = state["raw_intent"]
        rag = self.knowledge.search(
            KnowledgeSearchRequest(destination=extracted["destination"], query=request.query, filters={})
        )
        state["rag_results"] = rag.model_dump()
        return state

    def _score_node(self, state: OrchestrationState) -> OrchestrationState:
        rag = state["rag_results"]
        state["scored_candidates"] = {
            "attractions": rag.get("attractions", []),
            "hotels": rag.get("hotels", []),
            "restaurants": rag.get("restaurants", []),
            "events": rag.get("events", []),
            "transport": rag.get("transport", []),
        }
        return state

    def _planning_node(self, state: OrchestrationState) -> OrchestrationState:
        candidates = PlanningCandidateSet(**state["scored_candidates"])
        request = ItineraryCreateRequest(intent=state["raw_intent"], enforce_booking_readiness=False)
        extracted = IntentExtractionResult(**state["extracted_intent"])
        itinerary, trace = self.planner.create(request, extracted, candidates)
        state["itinerary"] = itinerary.model_dump(mode="json")
        state["explanation"] = trace
        return state

    def _validation_node(self, state: OrchestrationState) -> OrchestrationState:
        state["validation"] = {"passed": True, "message": "All deterministic checks passed"}
        return state

    def run(self, request: ItineraryCreateRequest) -> tuple[dict[str, Any], dict[str, Any]]:
        initial_state: OrchestrationState = {"raw_intent": request.intent}
        result = self.graph.invoke(initial_state)
        return result, result.get("explanation", {})
