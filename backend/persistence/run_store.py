"""Validated JSON persistence and replay support for simulation runs."""

from __future__ import annotations

from dataclasses import asdict
from math import isclose
from pathlib import Path
from typing import Any, Optional

import networkx as nx
from pydantic import BaseModel

from backend.config import PARAMETERS
from backend.intervention.policy_engine import (
    simulate_policy1_repayment_relief,
    simulate_policy2_transmission_severance,
    simulate_policy3_emergency_liquidity,
)
from backend.simulation.cascade_engine import SimulationState, run_cascade_simulation
from backend.simulation.shock import Shock


class RunRecord(BaseModel):
    """Persisted inputs and auditable outputs needed to reproduce one run."""

    run_id: str
    timestamp: str
    dataset_id: str
    dataset_version: str
    shock_configuration: dict
    model_parameters: dict
    distress_threshold: float
    policy_profile: str
    baseline_cascade_summary: dict
    criticality_rankings: list[dict]
    selected_intervention: Optional[dict] = None
    final_counterfactual_summary: Optional[dict] = None
    outcome_vector: Optional[dict] = None


def summarize_simulation_state(state: SimulationState) -> dict[str, Any]:
    """Produce a JSON-compatible state summary suitable for a ``RunRecord``."""
    return {
        "distressed_borrowers": sorted(
            borrower_id
            for borrower_id, stress_state in state.borrower_states.items()
            if stress_state.is_distressed
        ),
        "total_effective_stress": sum(
            stress_state.effective_stress
            for stress_state in state.borrower_states.values()
        ),
        "reached_nodes": sorted(state.reached_nodes),
        "activated_sources": sorted(state.activated_sources),
        "borrower_states": {
            borrower_id: asdict(stress_state)
            for borrower_id, stress_state in sorted(state.borrower_states.items())
        },
    }


def _values_match(expected: Any, actual: Any) -> bool:
    """Compare persisted values, allowing harmless floating-point roundoff."""
    if isinstance(expected, float) and isinstance(actual, (float, int)):
        return isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(expected, dict) and isinstance(actual, dict):
        return all(
            key in actual and _values_match(value, actual[key])
            for key, value in expected.items()
        )
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(
            _values_match(expected_item, actual_item)
            for expected_item, actual_item in zip(expected, actual)
        )
    return expected == actual


def _confirm_matches(label: str, stored: dict, actual: dict) -> None:
    if not _values_match(stored, actual):
        raise ValueError(f"Stored {label} does not match the reproduced result")


def _outcome_summary(
    baseline_state: SimulationState, final_state: SimulationState, cost: float
) -> dict[str, float]:
    baseline_distressed = sum(
        stress.is_distressed for stress in baseline_state.borrower_states.values()
    )
    final_distressed = sum(
        stress.is_distressed for stress in final_state.borrower_states.values()
    )
    baseline_stress = sum(
        stress.effective_stress for stress in baseline_state.borrower_states.values()
    )
    final_stress = sum(
        stress.effective_stress for stress in final_state.borrower_states.values()
    )
    return {
        "delta_distressed": float(baseline_distressed - final_distressed),
        "systemic_stress_relief": baseline_stress - final_stress,
        "reach_reduction": float(
            len(baseline_state.reached_nodes) - len(final_state.reached_nodes)
        ),
        "direct_financial_cost": cost,
    }


class RunStore:
    """Save, load, and replay immutable baseline/counterfactual run records."""

    @staticmethod
    def save_run(record: RunRecord, filepath: str) -> None:
        """Validate and serialize a run record as UTF-8 JSON."""
        Path(filepath).write_text(record.model_dump_json(indent=2), encoding="utf-8")

    @staticmethod
    def load_run(filepath: str) -> RunRecord:
        """Load JSON and parse it into a validated ``RunRecord``."""
        return RunRecord.model_validate_json(Path(filepath).read_text(encoding="utf-8"))

    @staticmethod
    def reproduce_run(
        run_record: RunRecord,
        graph: nx.DiGraph | nx.MultiDiGraph,
    ) -> tuple[SimulationState, SimulationState]:
        """Re-run the stored scenario and selected policy, verifying stored output."""
        if not isclose(
            run_record.distress_threshold,
            PARAMETERS.distress_threshold,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError("Stored distress threshold differs from active parameters")

        shock = Shock.model_validate(run_record.shock_configuration)
        baseline_state = run_cascade_simulation(graph, shock)
        _confirm_matches(
            "baseline cascade summary",
            run_record.baseline_cascade_summary,
            summarize_simulation_state(baseline_state),
        )

        selected = run_record.selected_intervention
        cost = 0.0
        if selected is None:
            final_state = run_cascade_simulation(graph, shock)
        else:
            policy = str(selected.get("policy", selected.get("policy_name", ""))).lower()
            borrower_id = selected.get("borrower_id", selected.get("target_borrower_id"))
            if not borrower_id:
                raise ValueError("Selected intervention must include borrower_id")

            if policy in {"policy1", "policy_1", "policy 1", "repayment_relief"}:
                result = simulate_policy1_repayment_relief(
                    graph,
                    baseline_state,
                    borrower_id,
                    float(selected["monthly_relief_amount"]),
                    int(selected["duration"]),
                )
                final_state, cost = result.simulation_state, result.total_cost
            elif policy in {
                "policy2",
                "policy_2",
                "policy 2",
                "transmission_severance",
            }:
                selected_edges = selected.get(
                    "selected_edge_set", selected.get("severed_edges")
                )
                if selected_edges is None:
                    policy2_result = simulate_policy2_transmission_severance(
                        graph,
                        baseline_state,
                        borrower_id,
                        run_record.policy_profile,
                    )
                    preset_name = selected.get("selected_preset", "Optimal Shield")
                    try:
                        final_state = policy2_result.presets[preset_name].simulation_state
                    except KeyError as error:
                        raise ValueError(
                            f"Unknown stored Policy 2 preset: {preset_name!r}"
                        ) from error
                else:
                    final_state = run_cascade_simulation(
                        graph, shock, edge_mask=set(selected_edges)
                    )
                cost = 0.0
            elif policy in {
                "policy3",
                "policy_3",
                "policy 3",
                "emergency_liquidity",
            }:
                result = simulate_policy3_emergency_liquidity(
                    graph, baseline_state, borrower_id, float(selected["M_cap"])
                )
                final_state, cost = result.simulation_state, result.total_cost
            else:
                raise ValueError(f"Unknown selected policy: {policy!r}")

        if run_record.final_counterfactual_summary is not None:
            _confirm_matches(
                "final counterfactual summary",
                run_record.final_counterfactual_summary,
                summarize_simulation_state(final_state),
            )
        if run_record.outcome_vector is not None:
            _confirm_matches(
                "outcome vector",
                run_record.outcome_vector,
                _outcome_summary(baseline_state, final_state, cost),
            )

        return baseline_state, final_state
