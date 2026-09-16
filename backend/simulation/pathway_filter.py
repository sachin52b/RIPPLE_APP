"""Step 4 filtering of relationship pathways relevant to a shock."""

from __future__ import annotations

from typing import Any

import networkx as nx

from backend.simulation.shock import Shock


RetainedEdge = tuple[str, str, Any, dict[str, Any]]


def _metadata_matches(
    edge_data: dict[str, Any], field_name: str, expected_value: str | None
) -> bool:
    """Match a shock context against a relationship field or its metadata."""
    if expected_value is None:
        return False

    metadata = edge_data.get("metadata", {})
    value = edge_data.get(field_name, metadata.get(field_name))
    if value == expected_value:
        return True

    plural_value = metadata.get(f"{field_name}s")
    return isinstance(plural_value, (list, tuple, set)) and expected_value in plural_value


def filter_relevant_edges(
    graph: nx.DiGraph | nx.MultiDiGraph, shock: Shock, source_node_id: str
) -> list[RetainedEdge]:
    """Return outgoing edges allowed to carry the specified shock onward.

    Each retained edge is returned as ``(source, target, key, attributes)``. For a
    regular ``DiGraph``, ``key`` is ``None``; a ``MultiDiGraph`` preserves its key.
    """
    if graph.is_multigraph():
        outgoing_edges = graph.out_edges(source_node_id, keys=True, data=True)
    else:
        outgoing_edges = (
            (source, target, None, data)
            for source, target, data in graph.out_edges(source_node_id, data=True)
        )

    retained_edges: list[RetainedEdge] = []
    for source, target, key, edge_data in outgoing_edges:
        mechanism = edge_data.get("super_mechanism")
        if mechanism in {"joint_liability", "formal_group"}:
            retained_edges.append((source, target, key, edge_data))
        elif (
            mechanism == "economic_exposure"
            and shock.cause == "market_shock"
            and _metadata_matches(
                edge_data, "economic_source_id", shock.economic_source_id
            )
        ):
            retained_edges.append((source, target, key, edge_data))
        elif (
            mechanism == "geographic_exposure"
            and shock.cause == "geographic_shock"
            and _metadata_matches(edge_data, "location_id", shock.location_id)
        ):
            retained_edges.append((source, target, key, edge_data))

    return retained_edges
