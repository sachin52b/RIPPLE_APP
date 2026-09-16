"""Borrower-level stress and distress evaluation (Step 3)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.config import PARAMETERS
from backend.data.schema import Borrower


@dataclass(frozen=True)
class BorrowerStressState:
    """Auditable results from evaluating one borrower under a shock."""

    post_shock_income: float
    required_amount: float
    monthly_deficit: float
    total_deficit: float
    cash_stress: float
    buffer_stress: float
    effective_stress: float
    is_distressed: bool


def evaluate_borrower_stress(
    borrower: Borrower,
    severity: float,
    duration: int,
    extra_monthly_obligation: float = 0.0,
) -> BorrowerStressState:
    """Evaluate the locked Step 3 formulas for a single borrower."""
    effective_duration = max(1, duration)
    post_shock_income = borrower.monthly_income * (1.0 - severity)
    total_loan_obligation = (
        borrower.monthly_loan_obligation + extra_monthly_obligation
    )
    required_amount = borrower.monthly_essential_expense + total_loan_obligation
    if required_amount <= 0:
        raise ValueError("Required amount must be greater than 0")

    monthly_deficit = max(0.0, required_amount - post_shock_income)
    cash_stress = monthly_deficit / required_amount
    total_deficit = monthly_deficit * effective_duration

    if total_deficit <= 0:
        buffer_stress = 0.0
    else:
        coverage = borrower.liquidity_buffer / total_deficit
        buffer_stress = 1.0 - min(1.0, coverage)

    effective_stress = max(
        cash_stress,
        PARAMETERS.cash_stress_weight * cash_stress
        + PARAMETERS.buffer_stress_weight * buffer_stress,
    )
    is_distressed = (
        cash_stress >= PARAMETERS.cash_stress_override
        or effective_stress >= PARAMETERS.distress_threshold
    )

    return BorrowerStressState(
        post_shock_income=post_shock_income,
        required_amount=required_amount,
        monthly_deficit=monthly_deficit,
        total_deficit=total_deficit,
        cash_stress=cash_stress,
        buffer_stress=buffer_stress,
        effective_stress=effective_stress,
        is_distressed=is_distressed,
    )
