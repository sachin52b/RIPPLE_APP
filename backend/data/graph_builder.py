"""Validation and directed network construction for portfolio data."""

from __future__ import annotations

from typing import Any

import networkx as nx

from backend.data.schema import Borrower, Relationship


class GraphBuilder:
    """Load validated portfolio records and construct an inspectable network."""

    @staticmethod
    def load_from_dicts(
        borrowers_raw: list[dict[str, Any]],
        relationships_raw: list[dict[str, Any]],
    ) -> tuple[list[Borrower], list[Relationship]]:
        """Validate raw records and ensure their identifiers are consistent."""
        borrowers = [Borrower.model_validate(record) for record in borrowers_raw]
        borrower_ids = [borrower.borrower_id for borrower in borrowers]
        duplicate_ids = sorted(
            borrower_id
            for borrower_id in set(borrower_ids)
            if borrower_ids.count(borrower_id) > 1
        )
        if duplicate_ids:
            raise ValueError(
                "Duplicate borrower_id values are not allowed: "
                + ", ".join(duplicate_ids)
            )

        relationships = [
            Relationship.model_validate(record) for record in relationships_raw
        ]
        borrower_id_set = set(borrower_ids)
        invalid_relationships = [
            relationship
            for relationship in relationships
            if relationship.source not in borrower_id_set
            or relationship.target not in borrower_id_set
        ]
        if invalid_relationships:
            details = ", ".join(
                f"{relationship.edge_id} "
                f"(source={relationship.source!r}, target={relationship.target!r})"
                for relationship in invalid_relationships
            )
            raise ValueError(
                "Relationships reference unknown borrower_id values: " + details
            )

        return borrowers, relationships

    @staticmethod
    def build_graph(
        borrowers: list[Borrower], relationships: list[Relationship]
    ) -> nx.MultiDiGraph:
        """Create a directed graph while retaining complete record metadata."""
        graph = nx.MultiDiGraph()

        for borrower in borrowers:
            graph.add_node(
                borrower.borrower_id,
                borrower=borrower,
                **borrower.model_dump(),
            )

        for relationship in relationships:
            graph.add_edge(
                relationship.source,
                relationship.target,
                relationship=relationship,
                **relationship.model_dump(),
            )

        return graph
