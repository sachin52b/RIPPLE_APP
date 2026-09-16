"""Local propagation calculations for the four supported mechanisms."""

from __future__ import annotations

from math import prod
from typing import Any

from backend.config import PARAMETERS
from backend.data.schema import Borrower
from backend.simulation.stress_engine import BorrowerStressState


def propagate_joint_liability(
    source_state: BorrowerStressState,
    target_borrower: Borrower,
    edge_data: dict[str, Any],
) -> float:
    """Return the contractually supported monthly burden transferred to a target."""
    del target_borrower  # The edge's contractual terms define this transfer.

    source_shortfall = source_state.monthly_deficit
    contractual_exposure = edge_data.get("contractual_monthly_exposure")
    liability_share = edge_data.get("liability_share")

    if contractual_exposure is not None:
        return min(source_shortfall, contractual_exposure)
    if liability_share is not None:
        share_transfer = source_shortfall * liability_share
        return min(
            share_transfer,
            edge_data.get("contractual_monthly_exposure", share_transfer),
        )

    raise ValueError(
        "Joint-liability propagation requires contractual_monthly_exposure "
        "or liability_share"
    )


def calculate_group_pressure(source_effective_stress: float, N_group: int) -> float:
    """Calculate one distressed member's non-monetary pressure on each peer."""
    if N_group <= 1:
        return 0.0
    return (source_effective_stress * PARAMETERS.gamma_group) / (N_group - 1)


def aggregate_group_pressures(pressures: list[float]) -> float:
    """Combine incoming group pressures with diminishing aggregation."""
    return 1.0 - prod(1.0 - pressure for pressure in pressures)


def apply_group_pressure_update(
    base_effective_stress: float, delta_total_pressure: float
) -> float:
    """Apply group pressure without altering the borrower's financial ledger."""
    return base_effective_stress + (1.0 - base_effective_stress) * delta_total_pressure


def _quantifiable_exposure_fraction(
    borrower: Borrower, edge_data: dict[str, Any]
) -> float | None:
    """Read a supplied economic fraction or derive it from source-level income."""
    metadata = edge_data.get("metadata", {})
    for field_name in (
        "exposure_fraction",
        "economic_exposure_fraction",
        "E_B",
    ):
        value = edge_data.get(field_name, metadata.get(field_name))
        if value is not None:
            return float(value)

    for field_name in ("income_from_shocked_source", "source_monthly_income"):
        source_income = edge_data.get(field_name, metadata.get(field_name))
        if source_income is not None and borrower.monthly_income > 0:
            return float(source_income) / borrower.monthly_income

    return None


def calculate_economic_income_loss(
    borrower: Borrower, shock_severity: float, edge_data: dict[str, Any]
) -> float:
    """Calculate measurable common-source income loss; never invent exposure."""
    exposure_fraction = _quantifiable_exposure_fraction(borrower, edge_data)
    if exposure_fraction is None:
        return 0.0
    return borrower.monthly_income * exposure_fraction * shock_severity


def calculate_geographic_income_loss(
    borrower: Borrower, shock_severity: float
) -> float:
    """Calculate the common-cause income loss for an affected location."""
    return borrower.monthly_income * shock_severity
