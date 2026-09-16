"""Outcome measurement, comparison, and evidence-based decision summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import networkx as nx

from backend.intervention.criticality_engine import calculate_criticality
from backend.intervention.policy_engine import (
    Policy1Result,
    Policy2Result,
    Policy3Result,
)
from backend.simulation.cascade_engine import SimulationState


@dataclass(frozen=True)
class OutcomeVector:
    """The common audit vector for every intervention counterfactual."""

    delta_distressed: float
    systemic_stress_relief: float
    reach_reduction: float
    direct_financial_cost: float


@dataclass(frozen=True)
class PolicyComparisonResult:
    policy_name: str
    outcome_vector: OutcomeVector
    delta_criticality: float
    efficiency_phi: Union[float, str]
    systemic_rank: int
    summary_text: str
    selected_preset: Optional[str] = None


def _distressed_count(state: SimulationState) -> int:
    return sum(stress_state.is_distressed for stress_state in state.borrower_states.values())


def _total_stress(state: SimulationState) -> float:
    return sum(stress_state.effective_stress for stress_state in state.borrower_states.values())


def calculate_outcome_vector(
    baseline_state: SimulationState,
    counterfactual_state: SimulationState,
    cost: float,
) -> OutcomeVector:
    """Calculate the uncollapsed [ΔD, ΔS, ΔR, Cost] audit vector."""
    return OutcomeVector(
        delta_distressed=_distressed_count(baseline_state)
        - _distressed_count(counterfactual_state),
        systemic_stress_relief=_total_stress(baseline_state)
        - _total_stress(counterfactual_state),
        reach_reduction=len(baseline_state.reached_nodes)
        - len(counterfactual_state.reached_nodes),
        direct_financial_cost=cost,
    )


def _summary_text(policy_name: str, outcome: OutcomeVector) -> str:
    return (
        f"{policy_name}: ΔD={outcome.delta_distressed}, "
        f"ΔS={outcome.systemic_stress_relief:.4f}, "
        f"ΔR={outcome.reach_reduction}, "
        f"direct cost={outcome.direct_financial_cost:.2f}."
    )


def compare_interventions(
    graph: nx.DiGraph | nx.MultiDiGraph,
    baseline_state: SimulationState,
    target_borrower_id: str,
    policy1_result: Policy1Result,
    policy2_result: Policy2Result,
    policy3_result: Policy3Result,
    profile_name: str = "BALANCED",
) -> list[PolicyComparisonResult]:
    """Compare three policy runs from one immutable baseline and target."""
    if target_borrower_id not in graph:
        raise ValueError(f"Unknown borrower_id: {target_borrower_id!r}")
    if any(
        result.borrower_id != target_borrower_id
        for result in (policy1_result, policy2_result, policy3_result)
    ):
        raise ValueError("All policy results must use target_borrower_id")

    optimal_shield = policy2_result.presets.get("Optimal Shield")
    if optimal_shield is None:
        raise ValueError("Policy 2 result must include an Optimal Shield preset")

    policy_runs = [
        (
            "Policy 1 — Repayment Relief",
            None,
            policy1_result.simulation_state,
            policy1_result.total_cost,
            False,
        ),
        (
            "Policy 2 — Transmission Severance",
            "Optimal Shield",
            optimal_shield.simulation_state,
            optimal_shield.cost,
            True,
        ),
        (
            "Policy 3 — Emergency Liquidity Support",
            None,
            policy3_result.simulation_state,
            policy3_result.total_cost,
            False,
        ),
    ]

    unranked_results: list[PolicyComparisonResult] = []
    for policy_name, preset_name, counterfactual_state, cost, is_non_cash in policy_runs:
        outcome = calculate_outcome_vector(
            baseline_state, counterfactual_state, cost
        )
        delta_criticality, _ = calculate_criticality(
            outcome.delta_distressed,
            outcome.systemic_stress_relief,
            profile_name,
        )
        efficiency: Union[float, str]
        if is_non_cash:
            efficiency = "N/A — non-cash intervention"
        else:
            efficiency = delta_criticality / max(1.0, outcome.direct_financial_cost)

        unranked_results.append(
            PolicyComparisonResult(
                policy_name=policy_name,
                selected_preset=preset_name,
                outcome_vector=outcome,
                delta_criticality=delta_criticality,
                efficiency_phi=efficiency,
                systemic_rank=0,
                summary_text=_summary_text(policy_name, outcome),
            )
        )

    ordered_results = sorted(
        unranked_results,
        key=lambda result: (-result.delta_criticality, result.policy_name),
    )
    return [
        PolicyComparisonResult(
            policy_name=result.policy_name,
            selected_preset=result.selected_preset,
            outcome_vector=result.outcome_vector,
            delta_criticality=result.delta_criticality,
            efficiency_phi=result.efficiency_phi,
            systemic_rank=rank,
            summary_text=result.summary_text,
        )
        for rank, result in enumerate(ordered_results, start=1)
    ]


def generate_decision_summary(
    baseline_state: SimulationState,
    selected_policy_result: PolicyComparisonResult,
    target_borrower_id: str,
) -> dict:
    """Return a human-readable before/after dictionary from recorded metrics only."""
    outcome = selected_policy_result.outcome_vector
    before_distressed = _distressed_count(baseline_state)
    before_stress = _total_stress(baseline_state)
    before_reach = len(baseline_state.reached_nodes)
    after_distressed = before_distressed - outcome.delta_distressed
    after_stress = before_stress - outcome.systemic_stress_relief
    after_reach = before_reach - outcome.reach_reduction

    return {
        "selected_policy": selected_policy_result.policy_name,
        "selected_preset": selected_policy_result.selected_preset,
        "target_borrower_id": target_borrower_id,
        "before": {
            "distressed_borrowers": before_distressed,
            "systemic_stress": before_stress,
            "cascade_reach": before_reach,
        },
        "after": {
            "distressed_borrowers": after_distressed,
            "systemic_stress": after_stress,
            "cascade_reach": after_reach,
        },
        "outcome_vector": {
            "delta_distressed": outcome.delta_distressed,
            "systemic_stress_relief": outcome.systemic_stress_relief,
            "reach_reduction": outcome.reach_reduction,
            "direct_financial_cost": outcome.direct_financial_cost,
        },
        "delta_criticality": selected_policy_result.delta_criticality,
        "efficiency_phi": selected_policy_result.efficiency_phi,
        "systemic_rank": selected_policy_result.systemic_rank,
        "summary_text": (
            f"{selected_policy_result.policy_name} for borrower "
            f"{target_borrower_id}: distressed borrowers {before_distressed} → "
            f"{after_distressed}; cascade reach {before_reach} → {after_reach}; "
            f"systemic stress {before_stress:.4f} → {after_stress:.4f}; "
            f"direct financial cost {outcome.direct_financial_cost:.2f}."
        ),
    }
