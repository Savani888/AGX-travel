import re

from app.schemas.api.contracts import ConfidenceScore, IntentExtractionResult, IntentRequest


class IntentExtractionService:
    def extract(self, request: IntentRequest) -> IntentExtractionResult:
        q = request.query.lower()

        def _keywords(text: str, mapping: dict[str, str]) -> list[str]:
            hits = []
            for keyword, label in mapping.items():
                if keyword in text and label not in hits:
                    hits.append(label)
            return hits

        budget = None
        budget_match = re.search(r"\$(\d+)", q)
        if not budget_match:
            budget_match = re.search(r"(\d+)\s*(?:usd|dollars?)", q)
        if not budget_match:
            budget_match = re.search(r"budget\s*(?:of|under)?\s*(\d+)", q)
        if budget_match:
            budget = float(budget_match.group(1))

        duration_days = 3
        duration_match = re.search(r"(\d+)\s*[- ]?day", q)
        if duration_match:
            duration_days = max(1, min(30, int(duration_match.group(1))))

        destination = "Unknown"
        for candidate in [
            "kyoto",
            "paris",
            "london",
            "tokyo",
            "rome",
            "barcelona",
            "dubai",
            "new york",
            "goa",
        ]:
            if candidate in q:
                destination = candidate.title()
                break
        if destination == "Unknown":
            dynamic_destination = re.search(
                r"(?:trip to|travel to|to|in)\s+([a-z][a-z\s]{1,30}?)(?:\s+for\b|\s+with\b|\s+under\b|\s+budget\b|$)",
                q,
            )
            if dynamic_destination:
                destination = dynamic_destination.group(1).strip().title()

        group_size = 1
        group_match = re.search(r"for\s+(\d+)\s+(?:adults?|people|travelers?)", q)
        if group_match:
            group_size = int(group_match.group(1))
        elif "family" in q:
            group_size = 4

        travel_style = _keywords(
            q,
            {
                "cultural": "cultural",
                "luxury": "luxury",
                "eco": "eco",
                "budget travel": "budget",
                "backpack": "budget",
                "family": "family",
                "food": "foodie",
            },
        )
        interests = _keywords(
            q,
            {
                "food": "food",
                "culture": "culture",
                "cultural": "culture",
                "temple": "temples",
                "history": "history",
                "beach": "beach",
                "museum": "museums",
                "eco": "eco-tourism",
            },
        )

        mobility_constraints: list[str] = []
        if "mobility" in q or "wheelchair" in q or "stroller" in q:
            mobility_constraints.append("mobility_assistance")

        pace = "balanced"
        if "slow" in q or "relaxed" in q:
            pace = "slow"
        if "fast" in q or "packed" in q:
            pace = "fast"

        profile = request.profile
        return IntentExtractionResult(
            destination=destination,
            duration_days=duration_days,
            budget=budget,
            group_size=profile.group_size if profile else group_size,
            travel_style=profile.preferences.travel_style if profile else travel_style,
            interests=profile.preferences.interests if profile else interests,
            mobility_constraints=profile.constraints.mobility_constraints if profile else mobility_constraints,
            season=profile.season if profile else None,
            pace=profile.preferences.pace if profile else pace,
            accommodation_preferences=profile.preferences.accommodation_preferences if profile else [],
            dining_preferences=profile.preferences.dining_preferences if profile else [],
            confidence_flags=[
                ConfidenceScore(metric="destination", score=0.8 if destination != "Unknown" else 0.3),
                ConfidenceScore(metric="duration", score=0.9),
            ],
        )
