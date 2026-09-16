"""Central registry for versioned, locked model parameters."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Mapping


@dataclass(frozen=True)
class CriticalityPolicyProfile:
    """Locked criticality settings for one MFI policy profile."""

    mu: float
    cap: float


@dataclass(frozen=True)
class LockedParameters:
    """Single source of truth for the model's locked parameters."""

    distress_threshold: float = 0.30
    cash_stress_override: float = 0.35
    cash_stress_weight: float = 0.70
    buffer_stress_weight: float = 0.30
    gamma_group: float = 0.15
    severance_penalty: float = 0.05
    criticality_profiles: Mapping[str, CriticalityPolicyProfile] = field(
        default_factory=lambda: MappingProxyType(
            {
                "STRICT": CriticalityPolicyProfile(mu=0.05, cap=0.50),
                "BALANCED": CriticalityPolicyProfile(mu=0.20, cap=1.25),
                "AGGRESSIVE": CriticalityPolicyProfile(mu=0.40, cap=2.50),
            }
        )
    )


PARAMETER_VERSION: Final[str] = "1.0"
PARAMETERS: Final[LockedParameters] = LockedParameters()
