import json
from pathlib import Path

from app.services.evaluation_service import EvaluationService


def main() -> None:
    scenarios_path = Path("data/scenarios/traveler_scenarios.json")
    scenarios = json.loads(scenarios_path.read_text())
    synthetic_reports = []
    for _ in scenarios:
        synthetic_reports.append(
            {
                "itinerary_quality": 0.81,
                "coverage": 0.78,
                "feasibility": 0.87,
                "diversity": 0.76,
                "adaptability": 0.8,
                "time_to_replan": 1.5,
                "replanning_success_rate": 0.84,
                "preference_alignment": 0.82,
                "trust": 0.79,
                "transparency": 0.86,
                "satisfaction": 0.8,
            }
        )

    metrics = EvaluationService().compute_metrics(synthetic_reports)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
