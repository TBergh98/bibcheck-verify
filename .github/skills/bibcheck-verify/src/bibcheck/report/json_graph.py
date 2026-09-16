import json
from pathlib import Path

from bibcheck.graph.traverse import Graph, graph_to_dict


def write_json(graph: Graph, path: str | Path) -> None:
    Path(path).write_text(json.dumps(graph_to_dict(graph), indent=2, ensure_ascii=True), encoding="utf-8")
