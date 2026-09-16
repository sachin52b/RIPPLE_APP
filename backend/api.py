"""FastAPI adapter for the deterministic financial-contagion backend pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

import networkx as nx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import PARAMETERS, PARAMETER_VERSION
from backend.data.demo_data import generate_demo_dataset
from backend.data.graph_builder import GraphBuilder
from backend.intervention.criticality_engine import calculate_criticality, rank_borrower_criticality
from backend.intervention.policy_engine import (
    Policy1Result,
    Policy2Result,
    Policy3Result,
    simulate_policy1_repayment_relief,
    simulate_policy2_transmission_severance,
    simulate_policy3_emergency_liquidity,
)
from backend.persistence.run_store import RunRecord, RunStore, summarize_simulation_state
from backend.reporting.comparison_engine import (
    PolicyComparisonResult,
    calculate_outcome_vector,
    compare_interventions,
    generate_decision_summary,
)
from backend.simulation.cascade_engine import SimulationState, run_cascade_simulation
from backend.simulation.shock import Shock


app = FastAPI(title="Financial Contagion Lab API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NetworkUploadRequest(BaseModel):
    borrowers: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    dataset_id: str = "custom"
    dataset_version: str = "1.0"


class ShockSimulationRequest(BaseModel):
    network_id: str
    shock: Shock


class CriticalityRequest(BaseModel):
    run_id: str
    profile_name: Literal["STRICT", "BALANCED", "AGGRESSIVE"] = "BALANCED"


class InterventionEvaluateRequest(BaseModel):
    run_id: str
    borrower_id: str
    monthly_relief_amount: float = Field(ge=0.0)
    relief_duration: int = Field(ge=0)
    M_cap: float = Field(ge=0.0)
    profile_name: Literal["STRICT", "BALANCED", "AGGRESSIVE"] = "BALANCED"


class InterventionCommitRequest(BaseModel):
    run_id: str
    policy: Literal["policy1", "policy2", "policy3"]
    policy2_preset: Literal["Surgical", "Optimal Shield", "Full Containment"] = (
        "Optimal Shield"
    )


class SaveRunRequest(BaseModel):
    run_id: str
    filename: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    parameters: dict[str, Any]


class NetworkResponse(BaseModel):
    network_id: str
    dataset_id: str
    dataset_version: str
    node_count: int
    edge_count: int
    borrowers: list[dict[str, Any]]
    relationships: list[dict[str, Any]]


class SimulationStateResponse(BaseModel):
    run_id: str
    shock_config: dict[str, Any]
    borrower_states: dict[str, dict[str, Any]]
    extra_monthly_obligations: dict[str, float]
    group_pressure_deltas: dict[str, list[float]]
    income_losses: dict[str, float]
    activated_sources: list[str]
    reached_nodes: list[str]
    propagation_events: list[dict[str, Any]]
    summary: dict[str, Any]


class CriticalityResponse(BaseModel):
    run_id: str
    profile_name: str
    rankings: list[dict[str, Any]]


class InterventionEvaluationResponse(BaseModel):
    run_id: str
    target_borrower_id: str
    policy1: dict[str, Any]
    policy2: dict[str, Any]
    policy3: dict[str, Any]
    comparison: list[dict[str, Any]]


class InterventionCommitResponse(BaseModel):
    run_id: str
    selected_intervention: dict[str, Any]
    final_state: SimulationStateResponse
    outcome_vector: dict[str, Any]
    decision_summary: dict[str, Any]


class PersistenceSaveResponse(BaseModel):
    run_id: str
    filepath: str
    record: dict[str, Any]


@dataclass
class _NetworkContext:
    graph: nx.MultiDiGraph
    dataset_id: str
    dataset_version: str


@dataclass
class _ExecutionContext:
    network_id: str
    baseline_state: SimulationState
    criticality_rankings: list[Any]
    policy_results: dict[str, Any]
    comparison_results: list[PolicyComparisonResult]
    selected_intervention: Optional[dict[str, Any]] = None
    final_state: Optional[SimulationState] = None


_networks: dict[str, _NetworkContext] = {}
_executions: dict[str, _ExecutionContext] = {}
_run_directory = Path(__file__).resolve().parent / "persistence" / "runs"


def _parameters_dict() -> dict[str, Any]:
    return {
        "version": PARAMETER_VERSION,
        "distress_threshold": PARAMETERS.distress_threshold,
        "cash_stress_override": PARAMETERS.cash_stress_override,
        "cash_stress_weight": PARAMETERS.cash_stress_weight,
        "buffer_stress_weight": PARAMETERS.buffer_stress_weight,
        "gamma_group": PARAMETERS.gamma_group,
        "severance_penalty": PARAMETERS.severance_penalty,
        "criticality_profiles": {
            name: asdict(profile)
            for name, profile in PARAMETERS.criticality_profiles.items()
        },
    }


def _state_payload(state: SimulationState) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "shock_config": state.shock_config.model_dump(),
        "borrower_states": {
            borrower_id: asdict(stress_state)
            for borrower_id, stress_state in state.borrower_states.items()
        },
        "extra_monthly_obligations": state.extra_monthly_obligations,
        "group_pressure_deltas": state.group_pressure_deltas,
        "income_losses": state.income_losses,
        "activated_sources": sorted(state.activated_sources),
        "reached_nodes": sorted(state.reached_nodes),
        "propagation_events": [asdict(event) for event in state.propagation_events],
        "summary": summarize_simulation_state(state),
    }


def _network_payload(network_id: str, context: _NetworkContext) -> dict[str, Any]:
    return {
        "network_id": network_id,
        "dataset_id": context.dataset_id,
        "dataset_version": context.dataset_version,
        "node_count": context.graph.number_of_nodes(),
        "edge_count": context.graph.number_of_edges(),
        "borrowers": [
            data["borrower"].model_dump()
            for _, data in sorted(context.graph.nodes(data=True))
        ],
        "relationships": [
            {key: value for key, value in edge_data.items() if key != "relationship"}
            for _, _, _, edge_data in context.graph.edges(keys=True, data=True)
        ],
    }


def _network_context(network_id: str) -> _NetworkContext:
    try:
        return _networks[network_id]
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Unknown network_id") from error


def _execution_context(run_id: str) -> _ExecutionContext:
    try:
        return _executions[run_id]
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Unknown run_id; execute /api/simulation/shock first",
        ) from error


def _store_graph(
    graph: nx.MultiDiGraph, dataset_id: str, dataset_version: str
) -> dict[str, Any]:
    network_id = f"network-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    context = _NetworkContext(graph, dataset_id, dataset_version)
    _networks[network_id] = context
    return _network_payload(network_id, context)


def _outcome_payload(outcome) -> dict[str, Any]:
    return asdict(outcome)


def _comparison_payload(result: PolicyComparisonResult) -> dict[str, Any]:
    return {
        "policy_name": result.policy_name,
        "selected_preset": result.selected_preset,
        "outcome_vector": _outcome_payload(result.outcome_vector),
        "delta_criticality": result.delta_criticality,
        "efficiency_phi": result.efficiency_phi,
        "systemic_rank": result.systemic_rank,
        "summary_text": result.summary_text,
    }


def _policy2_payload(result: Policy2Result) -> dict[str, Any]:
    return {
        "borrower_id": result.borrower_id,
        "eligible_edges": result.eligible_edges,
        "presets": {
            name: {
                "name": preset.name,
                "severed_edges": preset.severed_edges,
                "cost": preset.cost,
                "internal_score": preset.internal_score,
                "simulation_state": _state_payload(preset.simulation_state),
            }
            for name, preset in result.presets.items()
        },
    }


def _record_for_execution(execution: _ExecutionContext) -> RunRecord:
    network = _network_context(execution.network_id)
    baseline = execution.baseline_state
    final_state = execution.final_state
    outcome = None
    if final_state is not None:
        selected_policy = execution.selected_intervention["policy"]
        cost = 0.0
        if selected_policy == "policy1":
            cost = execution.policy_results["policy1"].total_cost
        elif selected_policy == "policy3":
            cost = execution.policy_results["policy3"].total_cost
        outcome = asdict(calculate_outcome_vector(baseline, final_state, cost))
    return RunRecord(
        run_id=baseline.run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        dataset_id=network.dataset_id,
        dataset_version=network.dataset_version,
        shock_configuration=baseline.shock_config.model_dump(),
        model_parameters=_parameters_dict(),
        distress_threshold=PARAMETERS.distress_threshold,
        policy_profile=(
            execution.selected_intervention or {}
        ).get("profile_name", "BALANCED"),
        baseline_cascade_summary=summarize_simulation_state(baseline),
        criticality_rankings=[asdict(score) for score in execution.criticality_rankings],
        selected_intervention=execution.selected_intervention,
        final_counterfactual_summary=(
            summarize_simulation_state(final_state) if final_state else None
        ),
        outcome_vector=outcome,
    )


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service status and active, centralized parameter configuration."""
    return {"status": "ok", "parameters": _parameters_dict()}


@app.get("/api/network/demo", response_model=NetworkResponse)
def load_demo_network() -> NetworkResponse:
    """Load and retain the validated built-in portfolio network."""
    borrowers_raw, relationships_raw = generate_demo_dataset()
    try:
        borrowers, relationships = GraphBuilder.load_from_dicts(
            borrowers_raw, relationships_raw
        )
        return _store_graph(
            GraphBuilder.build_graph(borrowers, relationships), "demo", "1.0"
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/network/upload", response_model=NetworkResponse)
def upload_network(request: NetworkUploadRequest) -> NetworkResponse:
    """Validate custom records and construct an inspectable network graph."""
    try:
        borrowers, relationships = GraphBuilder.load_from_dicts(
            request.borrowers, request.relationships
        )
        return _store_graph(
            GraphBuilder.build_graph(borrowers, relationships),
            request.dataset_id,
            request.dataset_version,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/simulation/shock", response_model=SimulationStateResponse)
def simulate_shock(request: ShockSimulationRequest) -> SimulationStateResponse:
    """Define a shock, execute the baseline cascade, and retain its audit log."""
    network = _network_context(request.network_id)
    try:
        baseline = run_cascade_simulation(network.graph, request.shock)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    _executions[baseline.run_id] = _ExecutionContext(
        network_id=request.network_id,
        baseline_state=baseline,
        criticality_rankings=[],
        policy_results={},
        comparison_results=[],
    )
    return _state_payload(baseline)


@app.post("/api/intervention/criticality", response_model=CriticalityResponse)
def evaluate_criticality(request: CriticalityRequest) -> CriticalityResponse:
    """Run Stage 1 benchmark containment counterfactuals for every borrower."""
    execution = _execution_context(request.run_id)
    graph = _network_context(execution.network_id).graph
    rankings = rank_borrower_criticality(
        graph, execution.baseline_state, request.profile_name
    )
    execution.criticality_rankings = rankings
    return {
        "run_id": request.run_id,
        "profile_name": request.profile_name,
        "rankings": [asdict(score) for score in rankings],
    }


@app.post(
    "/api/intervention/evaluate", response_model=InterventionEvaluationResponse
)
def evaluate_interventions(
    request: InterventionEvaluateRequest,
) -> InterventionEvaluationResponse:
    """Run all three Stage 2 policy counterfactuals from one baseline state."""
    execution = _execution_context(request.run_id)
    graph = _network_context(execution.network_id).graph
    try:
        policy1 = simulate_policy1_repayment_relief(
            graph,
            execution.baseline_state,
            request.borrower_id,
            request.monthly_relief_amount,
            request.relief_duration,
        )
        policy2 = simulate_policy2_transmission_severance(
            graph,
            execution.baseline_state,
            request.borrower_id,
            request.profile_name,
        )
        policy3 = simulate_policy3_emergency_liquidity(
            graph, execution.baseline_state, request.borrower_id, request.M_cap
        )
        comparison = compare_interventions(
            graph,
            execution.baseline_state,
            request.borrower_id,
            policy1,
            policy2,
            policy3,
            request.profile_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    execution.policy_results = {
        "policy1": policy1,
        "policy2": policy2,
        "policy3": policy3,
        "profile_name": request.profile_name,
    }
    execution.comparison_results = comparison
    return {
        "run_id": request.run_id,
        "target_borrower_id": request.borrower_id,
        "policy1": {
            "borrower_id": policy1.borrower_id,
            "monthly_relief_amount": policy1.monthly_relief_amount,
            "relief_duration": policy1.relief_duration,
            "total_cost": policy1.total_cost,
            "simulation_state": _state_payload(policy1.simulation_state),
        },
        "policy2": _policy2_payload(policy2),
        "policy3": {
            "borrower_id": policy3.borrower_id,
            "required_liquidity_L_star": policy3.required_liquidity_L_star,
            "M_cap": policy3.M_cap,
            "actual_injection_C_actual": policy3.actual_injection_C_actual,
            "remaining_shortfall": policy3.remaining_shortfall,
            "total_cost": policy3.total_cost,
            "simulation_state": _state_payload(policy3.simulation_state),
        },
        "comparison": [_comparison_payload(result) for result in comparison],
    }


@app.post("/api/intervention/commit", response_model=InterventionCommitResponse)
def commit_intervention(request: InterventionCommitRequest) -> InterventionCommitResponse:
    """Re-run the exact selected counterfactual from the immutable baseline."""
    execution = _execution_context(request.run_id)
    if not execution.policy_results:
        raise HTTPException(
            status_code=409,
            detail="Evaluate interventions before committing a final selection",
        )
    graph = _network_context(execution.network_id).graph
    baseline = execution.baseline_state
    profile_name = execution.policy_results["profile_name"]

    if request.policy == "policy1":
        evaluated: Policy1Result = execution.policy_results["policy1"]
        final_state = simulate_policy1_repayment_relief(
            graph,
            baseline,
            evaluated.borrower_id,
            evaluated.monthly_relief_amount,
            evaluated.relief_duration,
        ).simulation_state
        selected = {
            "policy": "policy1",
            "borrower_id": evaluated.borrower_id,
            "monthly_relief_amount": evaluated.monthly_relief_amount,
            "duration": evaluated.relief_duration,
            "profile_name": profile_name,
        }
        cost = evaluated.total_cost
        policy_name, preset = "Policy 1 — Repayment Relief", None
    elif request.policy == "policy2":
        evaluated: Policy2Result = execution.policy_results["policy2"]
        preset_result = evaluated.presets[request.policy2_preset]
        final_state = run_cascade_simulation(
            graph, baseline.shock_config, edge_mask=set(preset_result.severed_edges)
        )
        selected = {
            "policy": "policy2",
            "borrower_id": evaluated.borrower_id,
            "selected_preset": request.policy2_preset,
            "selected_edge_set": preset_result.severed_edges,
            "profile_name": profile_name,
        }
        cost = 0.0
        policy_name, preset = "Policy 2 — Transmission Severance", request.policy2_preset
    else:
        evaluated: Policy3Result = execution.policy_results["policy3"]
        final_state = simulate_policy3_emergency_liquidity(
            graph, baseline, evaluated.borrower_id, evaluated.M_cap
        ).simulation_state
        selected = {
            "policy": "policy3",
            "borrower_id": evaluated.borrower_id,
            "M_cap": evaluated.M_cap,
            "profile_name": profile_name,
        }
        cost = evaluated.total_cost
        policy_name, preset = "Policy 3 — Emergency Liquidity Support", None

    outcome = calculate_outcome_vector(baseline, final_state, cost)
    delta_criticality, _ = calculate_criticality(
        outcome.delta_distressed, outcome.systemic_stress_relief, profile_name
    )
    selected_comparison = PolicyComparisonResult(
        policy_name=policy_name,
        selected_preset=preset,
        outcome_vector=outcome,
        delta_criticality=delta_criticality,
        efficiency_phi=(
            "N/A — non-cash intervention"
            if request.policy == "policy2"
            else delta_criticality / max(1.0, cost)
        ),
        systemic_rank=0,
        summary_text="Final selected counterfactual.",
    )
    execution.selected_intervention = selected
    execution.final_state = final_state
    return {
        "run_id": request.run_id,
        "selected_intervention": selected,
        "final_state": _state_payload(final_state),
        "outcome_vector": _outcome_payload(outcome),
        "decision_summary": generate_decision_summary(
            baseline, selected_comparison, selected["borrower_id"]
        ),
    }


@app.post("/api/persistence/save", response_model=PersistenceSaveResponse)
def save_run(request: SaveRunRequest) -> PersistenceSaveResponse:
    """Persist the complete retained run under the API-owned run directory."""
    execution = _execution_context(request.run_id)
    record = _record_for_execution(execution)
    requested_name = request.filename or f"{record.run_id}.json"
    filename = Path(requested_name).name
    if not filename.endswith(".json"):
        filename += ".json"
    _run_directory.mkdir(parents=True, exist_ok=True)
    filepath = _run_directory / filename
    RunStore.save_run(record, str(filepath))
    return {"run_id": record.run_id, "filepath": str(filepath), "record": record.model_dump()}


@app.get("/api/persistence/runs")
def list_or_replay_runs(
    run_id: Optional[str] = Query(default=None),
    network_id: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    """List persisted records, or replay one with a retained matching network."""
    _run_directory.mkdir(parents=True, exist_ok=True)
    saved_files = sorted(_run_directory.glob("*.json"), key=lambda path: path.name)
    if run_id is None:
        records = []
        for filepath in saved_files:
            try:
                record = RunStore.load_run(str(filepath))
                records.append(
                    {
                        "run_id": record.run_id,
                        "timestamp": record.timestamp,
                        "dataset_id": record.dataset_id,
                        "dataset_version": record.dataset_version,
                        "has_selected_intervention": record.selected_intervention is not None,
                    }
                )
            except ValueError:
                continue
        return {"runs": records}

    filepath = next(
        (
            candidate
            for candidate in saved_files
            if RunStore.load_run(str(candidate)).run_id == run_id
        ),
        None,
    )
    if filepath is None:
        raise HTTPException(status_code=404, detail="Saved run_id not found")
    record = RunStore.load_run(str(filepath))
    if network_id is None:
        active = _executions.get(run_id)
        network_id = active.network_id if active else None
    if network_id is None:
        raise HTTPException(
            status_code=409,
            detail="network_id is required to replay a run after the original session ends",
        )
    graph = _network_context(network_id).graph
    try:
        baseline, final_state = RunStore.reproduce_run(record, graph)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {
        "record": record.model_dump(),
        "baseline_state": _state_payload(baseline),
        "final_state": _state_payload(final_state),
    }


# In a deployed container the React bundle is copied to frontend/dist. API
# routes are registered above, while this fallback makes the browser app and
# its API share one stable public origin.
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    _frontend_assets = _frontend_dist / "assets"
    if _frontend_assets.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=_frontend_assets),
            name="frontend-assets",
        )

    @app.get("/{frontend_path:path}", include_in_schema=False)
    def serve_frontend(frontend_path: str) -> FileResponse:
        """Serve the single-page frontend for non-API browser routes."""
        del frontend_path
        return FileResponse(_frontend_dist / "index.html")
