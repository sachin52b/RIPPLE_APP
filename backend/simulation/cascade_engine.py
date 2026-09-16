"""Deterministic, auditable cascade simulation orchestration."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, replace
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import networkx as nx

from backend.config import PARAMETERS
from backend.data.schema import Borrower
from backend.simulation.pathway_filter import filter_relevant_edges
from backend.simulation.propagation import (
    aggregate_group_pressures,
    apply_group_pressure_update,
    calculate_economic_income_loss,
    calculate_geographic_income_loss,
    calculate_group_pressure,
    propagate_joint_liability,
)
from backend.simulation.shock import Shock
from backend.simulation.stress_engine import BorrowerStressState, evaluate_borrower_stress


@dataclass(frozen=True)
class PropagationEvent:
    """An auditable record of one mechanism-specific transmission."""

    event_id: str
    source_borrower: str
    target_borrower: str
    super_mechanism: str
    specific_mechanism: str
    pre_state_target: dict
    impact_type: str
    impact_amount_or_delta: float
    post_state_target: dict


@dataclass
class SimulationState:
    """Mutable working state and final output of a cascade simulation."""

    run_id: str
    shock_config: Shock
    borrower_states: Dict[str, BorrowerStressState]
    extra_monthly_obligations: Dict[str, float]
    group_pressure_deltas: Dict[str, List[float]]
    income_losses: Dict[str, float]
    activated_sources: Set[str]
    reached_nodes: Set[str]
    propagation_events: List[PropagationEvent]


def _edge_value(edge_data: dict[str, Any], field_name: str) -> Any:
    """Read a relationship field from either its top level or metadata mapping."""
    metadata = edge_data.get("metadata", {})
    return edge_data.get(field_name, metadata.get(field_name))


def _edge_matches(edge_data: dict[str, Any], field_name: str, value: str | None) -> bool:
    return value is not None and _edge_value(edge_data, field_name) == value


def _all_edges(graph: nx.DiGraph | nx.MultiDiGraph):
    if graph.is_multigraph():
        return graph.edges(keys=True, data=True)
    return ((source, target, None, data) for source, target, data in graph.edges(data=True))


def _recompute_borrower_state(
    borrower_id: str, borrowers: dict[str, Borrower], state: SimulationState
) -> BorrowerStressState:
    borrower = borrowers[borrower_id]
    income_loss = state.income_losses[borrower_id]
    severity = income_loss / borrower.monthly_income if borrower.monthly_income else 0.0
    financial_state = evaluate_borrower_stress(
        borrower,
        severity=severity,
        duration=state.shock_config.duration,
        extra_monthly_obligation=state.extra_monthly_obligations[borrower_id],
    )

    total_group_pressure = aggregate_group_pressures(
        state.group_pressure_deltas[borrower_id]
    )
    effective_stress = apply_group_pressure_update(
        financial_state.effective_stress, total_group_pressure
    )
    result = replace(
        financial_state,
        effective_stress=effective_stress,
        is_distressed=(
            financial_state.cash_stress >= PARAMETERS.cash_stress_override
            or effective_stress >= PARAMETERS.distress_threshold
        ),
    )
    state.borrower_states[borrower_id] = result
    return result


def _group_size(graph: nx.DiGraph | nx.MultiDiGraph, source_node_id: str) -> int:
    group_id = graph.nodes[source_node_id].get("group_id")
    if group_id is None:
        return 0
    return sum(data.get("group_id") == group_id for _, data in graph.nodes(data=True))


def run_cascade_simulation(
    graph: nx.DiGraph | nx.MultiDiGraph,
    shock: Shock,
    edge_mask: Optional[Set[str]] = None,
) -> SimulationState:
    """Run a deterministic cascade from a validated shock configuration.

    ``edge_mask`` contains relationship ``edge_id`` values to exclude, enabling
    later transmission-severance counterfactuals without mutating the graph.
    """
    borrowers = {
        borrower_id: data["borrower"]
        for borrower_id, data in graph.nodes(data=True)
    }
    if len(borrowers) != graph.number_of_nodes() or not all(
        isinstance(borrower, Borrower) for borrower in borrowers.values()
    ):
        raise ValueError("Every graph node must include a Borrower under 'borrower'")

    zero_states = {
        borrower_id: evaluate_borrower_stress(
            borrower, severity=0.0, duration=shock.duration
        )
        for borrower_id, borrower in borrowers.items()
    }
    state = SimulationState(
        run_id=str(uuid4()),
        shock_config=shock,
        borrower_states=zero_states,
        extra_monthly_obligations={borrower_id: 0.0 for borrower_id in borrowers},
        group_pressure_deltas={borrower_id: [] for borrower_id in borrowers},
        income_losses={borrower_id: 0.0 for borrower_id in borrowers},
        activated_sources=set(),
        reached_nodes=set(),
        propagation_events=[],
    )

    initially_affected: set[str] = set()
    if shock.cause == "income_shock":
        if shock.target_borrower_id is None or shock.target_borrower_id not in borrowers:
            raise ValueError("income_shock requires a target_borrower_id in the graph")
        borrower = borrowers[shock.target_borrower_id]
        state.income_losses[borrower.borrower_id] = borrower.monthly_income * shock.severity
        initially_affected.add(borrower.borrower_id)
    elif shock.cause == "market_shock":
        for _, target, _, edge_data in _all_edges(graph):
            if (
                edge_data.get("super_mechanism") == "economic_exposure"
                and _edge_matches(
                    edge_data, "economic_source_id", shock.economic_source_id
                )
            ):
                state.income_losses[target] += calculate_economic_income_loss(
                    borrowers[target], shock.severity, edge_data
                )
                initially_affected.add(target)
    elif shock.cause == "geographic_shock":
        for borrower_id, borrower in borrowers.items():
            if borrower.location_id == shock.location_id:
                state.income_losses[borrower_id] = calculate_geographic_income_loss(
                    borrower, shock.severity
                )
                initially_affected.add(borrower_id)

    for borrower_id in initially_affected:
        _recompute_borrower_state(borrower_id, borrowers, state)

    source_queue = deque(
        sorted(
            borrower_id
            for borrower_id in initially_affected
            if state.borrower_states[borrower_id].is_distressed
        )
    )
    state.reached_nodes.update(initially_affected)
    excluded_edges = edge_mask or set()

    while source_queue:
        source_node_id = source_queue.popleft()
        if source_node_id in state.activated_sources:
            continue
        state.activated_sources.add(source_node_id)

        for source, target, edge_key, edge_data in filter_relevant_edges(
            graph, shock, source_node_id
        ):
            edge_id = edge_data.get("edge_id")
            if edge_id in excluded_edges or edge_key in excluded_edges:
                continue

            target_borrower = borrowers[target]
            pre_state = asdict(state.borrower_states[target])
            mechanism = edge_data["super_mechanism"]
            source_state = state.borrower_states[source]

            if mechanism == "joint_liability":
                impact = propagate_joint_liability(source_state, target_borrower, edge_data)
                state.extra_monthly_obligations[target] += impact
                impact_type = "extra_monthly_obligation"
            elif mechanism == "formal_group":
                impact = calculate_group_pressure(
                    source_state.effective_stress, _group_size(graph, source)
                )
                state.group_pressure_deltas[target].append(impact)
                impact_type = "group_pressure"
            elif mechanism == "economic_exposure":
                impact = calculate_economic_income_loss(
                    target_borrower, shock.severity, edge_data
                )
                state.income_losses[target] += impact
                impact_type = "monthly_income_loss"
            elif mechanism == "geographic_exposure":
                impact = calculate_geographic_income_loss(target_borrower, shock.severity)
                state.income_losses[target] += impact
                impact_type = "monthly_income_loss"
            else:
                continue

            post_state = _recompute_borrower_state(target, borrowers, state)
            state.reached_nodes.add(target)
            state.propagation_events.append(
                PropagationEvent(
                    event_id=f"event-{len(state.propagation_events) + 1}",
                    source_borrower=source,
                    target_borrower=target,
                    super_mechanism=mechanism,
                    specific_mechanism=edge_data["specific_mechanism"],
                    pre_state_target=pre_state,
                    impact_type=impact_type,
                    impact_amount_or_delta=impact,
                    post_state_target=asdict(post_state),
                )
            )

            if (
                post_state.is_distressed
                and target not in state.activated_sources
                and target not in source_queue
            ):
                source_queue.append(target)

    return state
