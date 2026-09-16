"""Isolated counterfactual simulations for the three locked interventions."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import networkx as nx

from backend.config import PARAMETERS
from backend.intervention.criticality_engine import calculate_criticality
from backend.simulation.cascade_engine import SimulationState, run_cascade_simulation


@dataclass(frozen=True)
class Policy1Result:
    borrower_id: str
    monthly_relief_amount: float
    relief_duration: int
    total_cost: float
    simulation_state: SimulationState


@dataclass(frozen=True)
class Policy2Preset:
    name: str
    severed_edges: list[str]
    cost: float
    internal_score: float
    simulation_state: SimulationState


@dataclass(frozen=True)
class Policy2Result:
    borrower_id: str
    eligible_edges: list[str]
    presets: dict[str, Policy2Preset]
    simulation_state: SimulationState


@dataclass(frozen=True)
class Policy3Result:
    borrower_id: str
    required_liquidity_L_star: float
    M_cap: float
    actual_injection_C_actual: float
    remaining_shortfall: float
    total_cost: float
    simulation_state: SimulationState


@dataclass(frozen=True)
class _Policy2Candidate:
    edge_ids: frozenset[str]
    internal_score: float
    simulation_state: SimulationState


def _validate_borrower_id(graph: nx.DiGraph | nx.MultiDiGraph, borrower_id: str) -> None:
    if borrower_id not in graph:
        raise ValueError(f"Unknown borrower_id: {borrower_id!r}")


def _graph_with_borrower_updates(
    graph: nx.DiGraph | nx.MultiDiGraph, borrower_id: str, **updates: Any
) -> nx.DiGraph | nx.MultiDiGraph:
    """Copy graph/node data, replacing one borrower model without source mutation."""
    _validate_borrower_id(graph, borrower_id)
    counterfactual_graph = graph.copy()
    borrower = graph.nodes[borrower_id].get("borrower")
    if borrower is None:
        raise ValueError("Target graph node must include a Borrower under 'borrower'")
    updated_borrower = borrower.model_copy(update=updates)
    counterfactual_graph.nodes[borrower_id]["borrower"] = updated_borrower
    counterfactual_graph.nodes[borrower_id].update(updated_borrower.model_dump())
    return counterfactual_graph


def simulate_policy1_repayment_relief(
    graph: nx.DiGraph | nx.MultiDiGraph,
    baseline_state: SimulationState,
    borrower_id: str,
    monthly_relief_amount: float,
    duration: int,
) -> Policy1Result:
    """Reduce only the target's monthly repayment obligation and re-simulate."""
    if monthly_relief_amount < 0:
        raise ValueError("monthly_relief_amount must be non-negative")
    if duration < 0:
        raise ValueError("duration must be non-negative")
    _validate_borrower_id(graph, borrower_id)

    original_borrower = graph.nodes[borrower_id]["borrower"]
    counterfactual_graph = _graph_with_borrower_updates(
        graph,
        borrower_id,
        monthly_loan_obligation=max(
            0.0, original_borrower.monthly_loan_obligation - monthly_relief_amount
        ),
    )
    simulation_state = run_cascade_simulation(
        counterfactual_graph, baseline_state.shock_config
    )
    return Policy1Result(
        borrower_id=borrower_id,
        monthly_relief_amount=monthly_relief_amount,
        relief_duration=duration,
        total_cost=monthly_relief_amount * duration,
        simulation_state=simulation_state,
    )


def _eligible_outgoing_edges(
    graph: nx.DiGraph | nx.MultiDiGraph, borrower_id: str
) -> list[str]:
    _validate_borrower_id(graph, borrower_id)
    if graph.is_multigraph():
        outgoing_edges = graph.out_edges(borrower_id, keys=True, data=True)
        return sorted(
            edge_data["edge_id"]
            for _, _, _, edge_data in outgoing_edges
            if edge_data.get("super_mechanism") in {"joint_liability", "formal_group"}
        )
    return sorted(
        edge_data["edge_id"]
        for _, _, edge_data in graph.out_edges(borrower_id, data=True)
        if edge_data.get("super_mechanism") in {"joint_liability", "formal_group"}
    )


def _policy2_candidate(
    graph: nx.DiGraph | nx.MultiDiGraph,
    baseline_state: SimulationState,
    edge_ids: frozenset[str],
    profile_name: str,
) -> _Policy2Candidate:
    """Run a severance mask and compute its non-monetary internal score."""
    simulation_state = run_cascade_simulation(
        graph, baseline_state.shock_config, edge_mask=set(edge_ids)
    )
    baseline_distressed = sum(
        stress.is_distressed for stress in baseline_state.borrower_states.values()
    )
    counterfactual_distressed = sum(
        stress.is_distressed for stress in simulation_state.borrower_states.values()
    )
    baseline_stress = sum(
        stress.effective_stress for stress in baseline_state.borrower_states.values()
    )
    counterfactual_stress = sum(
        stress.effective_stress for stress in simulation_state.borrower_states.values()
    )
    delta_criticality, _ = calculate_criticality(
        baseline_distressed - counterfactual_distressed,
        baseline_stress - counterfactual_stress,
        profile_name,
    )
    return _Policy2Candidate(
        edge_ids=edge_ids,
        internal_score=delta_criticality
        - PARAMETERS.severance_penalty * len(edge_ids),
        simulation_state=simulation_state,
    )


def _best_candidate(candidates: list[_Policy2Candidate]) -> _Policy2Candidate:
    return max(
        candidates,
        key=lambda candidate: (
            candidate.internal_score,
            -len(candidate.edge_ids),
            tuple(sorted(candidate.edge_ids)),
        ),
    )


def simulate_policy2_transmission_severance(
    graph: nx.DiGraph | nx.MultiDiGraph,
    baseline_state: SimulationState,
    borrower_id: str,
    profile_name: str = "BALANCED",
) -> Policy2Result:
    """Evaluate severable outgoing edges without modifying the source graph."""
    eligible_edges = _eligible_outgoing_edges(graph, borrower_id)
    candidate_cache: dict[frozenset[str], _Policy2Candidate] = {}

    def evaluate(edge_ids: frozenset[str]) -> _Policy2Candidate:
        if edge_ids not in candidate_cache:
            candidate_cache[edge_ids] = _policy2_candidate(
                graph, baseline_state, edge_ids, profile_name
            )
        return candidate_cache[edge_ids]

    empty_set = frozenset()
    evaluate(empty_set)
    if len(eligible_edges) <= 8:
        for size in range(1, len(eligible_edges) + 1):
            for subset in combinations(eligible_edges, size):
                evaluate(frozenset(subset))
    else:
        selected = empty_set
        current = evaluate(selected)
        remaining = set(eligible_edges)
        while remaining:
            additions = [evaluate(selected | {edge_id}) for edge_id in remaining]
            best_addition = _best_candidate(additions)
            marginal_improvement = best_addition.internal_score - current.internal_score
            if marginal_improvement < 0.05:
                break
            selected = best_addition.edge_ids
            current = best_addition
            remaining -= selected

    full_containment = evaluate(frozenset(eligible_edges))
    all_candidates = list(candidate_cache.values())
    optimal_shield = _best_candidate(all_candidates)
    surgical_candidates = [
        candidate for candidate in all_candidates if len(candidate.edge_ids) == 1
    ]
    surgical = _best_candidate(surgical_candidates) if surgical_candidates else evaluate(empty_set)

    def preset(name: str, candidate: _Policy2Candidate) -> Policy2Preset:
        return Policy2Preset(
            name=name,
            severed_edges=sorted(candidate.edge_ids),
            cost=0.0,
            internal_score=candidate.internal_score,
            simulation_state=candidate.simulation_state,
        )

    presets = {
        "Surgical": preset("Surgical", surgical),
        "Optimal Shield": preset("Optimal Shield", optimal_shield),
        "Full Containment": preset("Full Containment", full_containment),
    }
    return Policy2Result(
        borrower_id=borrower_id,
        eligible_edges=eligible_edges,
        presets=presets,
        simulation_state=presets["Optimal Shield"].simulation_state,
    )


def simulate_policy3_emergency_liquidity(
    graph: nx.DiGraph | nx.MultiDiGraph,
    baseline_state: SimulationState,
    borrower_id: str,
    M_cap: float,
) -> Policy3Result:
    """Inject analytically required liquidity, bounded by the user budget cap."""
    if M_cap < 0:
        raise ValueError("M_cap must be non-negative")
    _validate_borrower_id(graph, borrower_id)

    borrower = graph.nodes[borrower_id]["borrower"]
    target_stress = baseline_state.borrower_states[borrower_id]
    target_deficit = target_stress.monthly_deficit * max(
        1, baseline_state.shock_config.duration
    )
    required_liquidity = max(0.0, target_deficit - borrower.liquidity_buffer)
    actual_injection = min(required_liquidity, M_cap)
    remaining_shortfall = max(0.0, required_liquidity - M_cap)

    counterfactual_graph = _graph_with_borrower_updates(
        graph,
        borrower_id,
        liquidity_buffer=borrower.liquidity_buffer + actual_injection,
    )
    simulation_state = run_cascade_simulation(
        counterfactual_graph, baseline_state.shock_config
    )
    return Policy3Result(
        borrower_id=borrower_id,
        required_liquidity_L_star=required_liquidity,
        M_cap=M_cap,
        actual_injection_C_actual=actual_injection,
        remaining_shortfall=remaining_shortfall,
        total_cost=actual_injection,
        simulation_state=simulation_state,
    )
