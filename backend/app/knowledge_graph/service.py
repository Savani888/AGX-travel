from collections import defaultdict
from typing import Any

from app.knowledge_graph.schema import KGEdge, KGNode


class TourismKnowledgeGraphService:
    def __init__(self) -> None:
        self.nodes: dict[str, KGNode] = {}
        self.edges: list[KGEdge] = []
        self.adj: dict[str, list[KGEdge]] = defaultdict(list)

    def ingest_entities(self, entities: list[dict[str, Any]]) -> None:
        for entity in entities:
            node_id = entity["id"]
            node_type = entity.get("entity_type", entity.get("category", "Entity"))
            self.nodes[node_id] = KGNode(node_id=node_id, node_type=node_type, properties=entity)
            destination = entity.get("destination")
            if destination:
                dest_id = f"dest::{destination.lower()}"
                if dest_id not in self.nodes:
                    self.nodes[dest_id] = KGNode(node_id=dest_id, node_type="Destination", properties={"name": destination})
                self._add_edge(node_id, dest_id, "LOCATED_IN")

    def _add_edge(self, source: str, target: str, relation: str, properties: dict | None = None) -> None:
        edge = KGEdge(source=source, target=target, relation=relation, properties=properties or {})
        self.edges.append(edge)
        self.adj[source].append(edge)

    def enrich_proximity(self) -> None:
        ids = [node_id for node_id in self.nodes if not node_id.startswith("dest::")]
        for left in ids:
            for right in ids:
                if left != right and left[:2] == right[:2]:
                    self._add_edge(left, right, "ALTERNATIVE_TO")

    def alternatives_for(self, node_id: str) -> list[dict[str, Any]]:
        edges = [edge for edge in self.adj.get(node_id, []) if edge.relation == "ALTERNATIVE_TO"]
        return [self.nodes[edge.target].properties for edge in edges[:5] if edge.target in self.nodes]
