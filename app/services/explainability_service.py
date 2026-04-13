from sqlalchemy.orm import Session

from app.models.explanation import ExplanationTraceRecord
from app.repositories.explanation_repository import ExplanationRepository
from app.schemas.api.contracts import ExplanationTrace


class ExplainabilityService:
    def __init__(self, db: Session | None = None):
        self.repo = ExplanationRepository(db) if db else None

    def store(self, itinerary_id: str, summary: str, decision_trace: dict, confidence: list[dict]) -> str:
        if not self.repo:
            return ""
        row = self.repo.create(
            ExplanationTraceRecord(
                itinerary_id=itinerary_id,
                stage="planning",
                trace_payload={
                    "summary": summary,
                    "decision_trace": decision_trace,
                    "confidence": confidence,
                },
            )
        )
        return row.id

    def list_for_itinerary(self, itinerary_id: str) -> list[ExplanationTrace]:
        if not self.repo:
            return []
        rows = self.repo.list_by_itinerary(itinerary_id)

        if not rows:
            return []

        def _as_list(value):
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                return [value]
            return []

        result: list[ExplanationTrace] = []
        for row in rows:
            trace = row.trace_payload.get("decision_trace", {}) if isinstance(row.trace_payload, dict) else {}
            try:
                item = ExplanationTrace(
                    itinerary_id=row.itinerary_id,
                    summary=(row.trace_payload or {}).get("summary", ""),
                    confidence=(row.trace_payload or {}).get("confidence", []),
                    decision_trace={
                        "candidate_pool": _as_list(trace.get("candidate_pool", [])),
                        "retrieved_evidence": _as_list(trace.get("retrieved_evidence", [])),
                        "ranking_scores": _as_list(trace.get("ranking_scores", [])),
                        "constraint_checks": _as_list(trace.get("constraint_checks", [])),
                        "selected_option": trace.get("selected_option", {}) if isinstance(trace, dict) else {},
                        "rejected_alternatives": _as_list(trace.get("rejected_alternatives", [])),
                        "contextual_factors": trace.get("contextual_factors", []) if isinstance(trace, dict) else [],
                    },
                )
            except Exception:
                item = ExplanationTrace(
                    itinerary_id=row.itinerary_id,
                    summary="Explanation trace unavailable; returning fallback summary.",
                    confidence=[],
                    decision_trace={
                        "candidate_pool": [],
                        "retrieved_evidence": [],
                        "ranking_scores": [],
                        "constraint_checks": [],
                        "selected_option": {},
                        "rejected_alternatives": [],
                        "contextual_factors": [],
                    },
                )
            result.append(item)
        return result
