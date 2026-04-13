from typing import Any


def build_explanation_text(trace: dict[str, Any]) -> str:
    selected = trace.get("selected_option", {})
    factors = ", ".join(trace.get("contextual_factors", []))
    return f"Selected {selected} based on constraints and context: {factors}".strip()
