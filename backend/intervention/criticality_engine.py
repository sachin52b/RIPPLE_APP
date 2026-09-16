"""Counterfactual borrower criticality ranking (the WHO stage)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx

from backend.config import PARAMETERS
from backend.simulation.cascade_engine import SimulationState, run_cascade_simulation


@dataclass(frozen=True)
class CriticalityScore:
    """A borrower's ranked structural importance under a policy profile."""

    borrower_id: str
    rank: int
    criticality: float
    delta_distressed: float
    systemic_stress_delta: float
    bounded_stress_component: float


def calculate_criticality(
    delta_distressed: float,
    systemic_stress_delta: float,
    profile_name: str = "BALANCED",
) -> tuple[float, float]:
    """Apply the locked bounded linear criticality formula.

    The calculation deliberately uses no logarithmic transformation: negative
    systemic stress deltas remain valid and reduce the resulting score.
    """
    profile_key = profile_name.upper()
    try:
        profile = PARAMETERS.criticality_profiles[profile_key]
    except KeyError as error:
        valid_profiles = ", ".join(PARAMETERS.criticality_profiles)
        raise ValueError(
            f"Unknown criticality profile {profile_name!r}; expected one of {valid_profiles}"
        ) from error

    bounded_stress_component = min(
        profile.mu * systemic_stress_delta,
        profile.cap,
    )
    criticality = delta_distressed + bounded_stress_component
    return criticality, bounded_stress_component


def _outgoing_edge_ids(
    graph: nx.DiGraph | nx.MultiDiGraph, borrower_id: str
) -> set[Any]:
    """Return all outgoing relationship IDs without changing the source graph."""
    if graph.is_multigraph():
        return {
            edge_data.get("edge_id", edge_key)
            for _, _, edge_key, edge_data in graph.out_edges(
                borrower_id, keys=True, data=True
            )
        }
    return {
        edge_data.get("edge_id")
        for _, _, edge_data in graph.out_edges(borrower_id, data=True)
    }


def rank_borrower_criticality(
    graph: nx.DiGraph | nx.MultiDiGraph,
    baseline_state: SimulationState,
    profile_name: str = "BALANCED",
    exclude_direct_income_shock_target: bool = True,
) -> list[CriticalityScore]:
    """Rank actionable borrowers by an isolated containment counterfactual.

    Each run masks only the candidate's outgoing relationships. The graph and
    supplied baseline state are read-only inputs and are never mutated. For a
    direct income shock, the externally shocked borrower is excluded by default:
    it is the observed incident origin, not a competing containment decision.
    This keeps the WHO stage focused on the best downstream intervention point.
    """
    baseline_distressed = sum(
        stress_state.is_distressed
        for stress_state in baseline_state.borrower_states.values()
    )
    baseline_total_stress = sum(
        stress_state.effective_stress
        for stress_state in baseline_state.borrower_states.values()
    )

    candidate_borrower_ids = list(graph.nodes)
    shock = baseline_state.shock_config
    if (
        exclude_direct_income_shock_target
        and shock.cause == "income_shock"
        and shock.target_borrower_id is not None
    ):
        candidate_borrower_ids = [
            borrower_id
            for borrower_id in candidate_borrower_ids
            if borrower_id != shock.target_borrower_id
        ]

    unranked_scores: list[CriticalityScore] = []
    for borrower_id in candidate_borrower_ids:
        counterfactual_state = run_cascade_simulation(
            graph,
            baseline_state.shock_config,
            edge_mask=_outgoing_edge_ids(graph, borrower_id),
        )
        counterfactual_distressed = sum(
            stress_state.is_distressed
            for stress_state in counterfactual_state.borrower_states.values()
        )
        counterfactual_total_stress = sum(
            stress_state.effective_stress
            for stress_state in counterfactual_state.borrower_states.values()
        )
        delta_distressed = baseline_distressed - counterfactual_distressed
        systemic_stress_delta = baseline_total_stress - counterfactual_total_stress
        criticality, bounded_component = calculate_criticality(
            delta_distressed, systemic_stress_delta, profile_name
        )
        unranked_scores.append(
            CriticalityScore(
                borrower_id=borrower_id,
                rank=0,
                criticality=criticality,
                delta_distressed=delta_distressed,
                systemic_stress_delta=systemic_stress_delta,
                bounded_stress_component=bounded_component,
            )
        )

    ordered_scores = sorted(
        unranked_scores,
        key=lambda score: (-score.criticality, score.borrower_id),
    )
    return [
        CriticalityScore(
            borrower_id=score.borrower_id,
            rank=rank,
            criticality=score.criticality,
            delta_distressed=score.delta_distressed,
            systemic_stress_delta=score.systemic_stress_delta,
            bounded_stress_component=score.bounded_stress_component,
        )
        for rank, score in enumerate(ordered_scores, start=1)
    ]
