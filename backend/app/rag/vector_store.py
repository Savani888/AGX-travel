from pathlib import Path
from typing import Any


class TourismVectorStore:
    """Simple embedding-free scorer placeholder that can be swapped with ChromaDB/Qdrant."""

    def __init__(self, dataset_path: str = "data/scenarios/knowledge_base.json") -> None:
        self.dataset_path = Path(dataset_path)
        self.entries = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if not self.dataset_path.exists():
            return []
        import json

        return json.loads(self.dataset_path.read_text())

    def query(self, destination: str, text: str, k: int = 20) -> list[dict[str, Any]]:
        tokens = set(text.lower().split())

        def score(entry: dict[str, Any]) -> float:
            hay = " ".join(
                [entry.get("name", ""), " ".join(entry.get("tags", [])), entry.get("category", "")]
            ).lower()
            return len(tokens.intersection(set(hay.split()))) + (1 if entry.get("destination") == destination else 0)

        ranked = sorted(self.entries, key=score, reverse=True)
        return [row for row in ranked if row.get("destination") == destination][:k]
