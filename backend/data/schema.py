"""Pydantic schemas for borrower records and network relationships."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


class Borrower(BaseModel):
    """A borrower node supplied by institutional portfolio data."""

    borrower_id: str
    group_id: Optional[str] = None
    location_id: str
    livelihood_type: str
    monthly_income: float = Field(ge=0)
    monthly_essential_expense: float = Field(ge=0)
    monthly_loan_obligation: float = Field(ge=0)
    outstanding_loan: float = Field(ge=0)
    liquidity_buffer: float = Field(ge=0)
    income_stability: Union[float, str]

    @model_validator(mode="after")
    def required_monthly_amount_is_positive(self) -> "Borrower":
        """Ensure the stress engine has a positive required monthly amount."""
        required = self.monthly_essential_expense + self.monthly_loan_obligation
        if required <= 0:
            raise ValueError(
                "monthly_essential_expense + monthly_loan_obligation must be greater than 0"
            )
        return self


class Relationship(BaseModel):
    """An explainable connection between two borrower nodes."""

    edge_id: str
    super_mechanism: Literal[
        "joint_liability",
        "formal_group",
        "economic_exposure",
        "geographic_exposure",
    ]
    specific_mechanism: str
    source: str
    target: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    contractual_monthly_exposure: Optional[float] = None
    liability_share: Optional[float] = None
    economic_source_type: Optional[str] = None
    economic_source_id: Optional[str] = None
