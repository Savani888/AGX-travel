from dataclasses import dataclass, field


@dataclass
class KGNode:
    node_id: str
    node_type: str
    properties: dict = field(default_factory=dict)


@dataclass
class KGEdge:
    source: str
    target: str
    relation: str
    properties: dict = field(default_factory=dict)
