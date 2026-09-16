"""Validated user-defined shock inputs."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Shock(BaseModel):
    """A borrower-specific or common-cause shock scenario."""

    shock_id: str
    cause: Literal["income_shock", "market_shock", "geographic_shock"]
    target_borrower_id: Optional[str] = None
    economic_source_id: Optional[str] = None
    location_id: Optional[str] = None
    severity: float = Field(ge=0.0, le=1.0)
    duration: int = Field(ge=0)
