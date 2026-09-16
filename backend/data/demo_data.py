"""A deliberately multi-wave demo portfolio for the contagion laboratory."""

from __future__ import annotations

from typing import Any


def generate_demo_dataset() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return an 18-borrower portfolio with contagion and resilience clusters.

    B10 is the isolated shock origin. B05 is the high-reach containment point:
    once activated, it fans stress into three branches which create successive
    propagation waves. B15–B18 form a well-buffered satellite group: it gives
    the canvas a realistic resilient segment and demonstrates containment.
    """
    borrowers = [
        {"borrower_id": "B01", "group_id": "G1", "location_id": "L1", "livelihood_type": "Weaving", "monthly_income": 11000, "monthly_essential_expense": 6200, "monthly_loan_obligation": 4600, "outstanding_loan": 42000, "liquidity_buffer": 220, "income_stability": 0.40},
        {"borrower_id": "B02", "group_id": "G1", "location_id": "L1", "livelihood_type": "Tailoring", "monthly_income": 12000, "monthly_essential_expense": 6900, "monthly_loan_obligation": 4900, "outstanding_loan": 44000, "liquidity_buffer": 250, "income_stability": 0.45},
        {"borrower_id": "B03", "group_id": "G1", "location_id": "L1", "livelihood_type": "Retail", "monthly_income": 10500, "monthly_essential_expense": 5900, "monthly_loan_obligation": 4400, "outstanding_loan": 38000, "liquidity_buffer": 180, "income_stability": 0.35},
        {"borrower_id": "B04", "group_id": "G1", "location_id": "L1", "livelihood_type": "Dairy", "monthly_income": 9800, "monthly_essential_expense": 5400, "monthly_loan_obligation": 4200, "outstanding_loan": 33000, "liquidity_buffer": 140, "income_stability": 0.35},
        {"borrower_id": "B05", "group_id": "G2", "location_id": "L1", "livelihood_type": "Milk collection", "monthly_income": 13000, "monthly_essential_expense": 7500, "monthly_loan_obligation": 5300, "outstanding_loan": 52000, "liquidity_buffer": 220, "income_stability": 0.40},
        {"borrower_id": "B06", "group_id": "G2", "location_id": "L1", "livelihood_type": "Dairy", "monthly_income": 10000, "monthly_essential_expense": 6000, "monthly_loan_obligation": 3700, "outstanding_loan": 36000, "liquidity_buffer": 120, "income_stability": 0.35},
        {"borrower_id": "B07", "group_id": "G2", "location_id": "L1", "livelihood_type": "Agriculture", "monthly_income": 9500, "monthly_essential_expense": 5100, "monthly_loan_obligation": 4100, "outstanding_loan": 31000, "liquidity_buffer": 130, "income_stability": 0.30},
        {"borrower_id": "B08", "group_id": "G2", "location_id": "L1", "livelihood_type": "Retail", "monthly_income": 9000, "monthly_essential_expense": 4900, "monthly_loan_obligation": 3900, "outstanding_loan": 29000, "liquidity_buffer": 120, "income_stability": 0.30},
        {"borrower_id": "B09", "group_id": "G2", "location_id": "L1", "livelihood_type": "Agriculture", "monthly_income": 9200, "monthly_essential_expense": 5000, "monthly_loan_obligation": 4000, "outstanding_loan": 30000, "liquidity_buffer": 120, "income_stability": 0.30},
        {"borrower_id": "B10", "group_id": "G3", "location_id": "L2", "livelihood_type": "Pottery", "monthly_income": 12000, "monthly_essential_expense": 6000, "monthly_loan_obligation": 4000, "outstanding_loan": 35000, "liquidity_buffer": 400, "income_stability": 0.50},
        {"borrower_id": "B11", "group_id": "G1", "location_id": "L1", "livelihood_type": "Food stall", "monthly_income": 10200, "monthly_essential_expense": 5700, "monthly_loan_obligation": 4300, "outstanding_loan": 34000, "liquidity_buffer": 150, "income_stability": 0.35},
        {"borrower_id": "B12", "group_id": "G3", "location_id": "L2", "livelihood_type": "Transport", "monthly_income": 10800, "monthly_essential_expense": 6100, "monthly_loan_obligation": 4500, "outstanding_loan": 37000, "liquidity_buffer": 160, "income_stability": 0.40},
        {"borrower_id": "B13", "group_id": "G1", "location_id": "L1", "livelihood_type": "Tailoring", "monthly_income": 9300, "monthly_essential_expense": 5100, "monthly_loan_obligation": 4000, "outstanding_loan": 28000, "liquidity_buffer": 110, "income_stability": 0.30},
        {"borrower_id": "B14", "group_id": "G2", "location_id": "L1", "livelihood_type": "Agriculture", "monthly_income": 9700, "monthly_essential_expense": 5300, "monthly_loan_obligation": 4200, "outstanding_loan": 32000, "liquidity_buffer": 130, "income_stability": 0.30},
        # A credible, visibly connected resilient satellite cluster.
        {"borrower_id": "B15", "group_id": "G4", "location_id": "L3", "livelihood_type": "Fisheries cooperative", "monthly_income": 22000, "monthly_essential_expense": 8000, "monthly_loan_obligation": 4000, "outstanding_loan": 30000, "liquidity_buffer": 12000, "income_stability": 0.85},
        {"borrower_id": "B16", "group_id": "G4", "location_id": "L3", "livelihood_type": "Cold-chain logistics", "monthly_income": 19500, "monthly_essential_expense": 7200, "monthly_loan_obligation": 4300, "outstanding_loan": 34000, "liquidity_buffer": 9000, "income_stability": 0.80},
        {"borrower_id": "B17", "group_id": "G4", "location_id": "L3", "livelihood_type": "Marine retail", "monthly_income": 18000, "monthly_essential_expense": 6800, "monthly_loan_obligation": 3900, "outstanding_loan": 29000, "liquidity_buffer": 7600, "income_stability": 0.78},
        {"borrower_id": "B18", "group_id": "G4", "location_id": "L3", "livelihood_type": "Net fabrication", "monthly_income": 17000, "monthly_essential_expense": 6500, "monthly_loan_obligation": 3800, "outstanding_loan": 27000, "liquidity_buffer": 7000, "income_stability": 0.75},
    ]

    relationships = [
        # The B10 spark reaches two independently vulnerable conduits.
        {"edge_id": "E01", "super_mechanism": "joint_liability", "specific_mechanism": "peripheral_spark_to_bottleneck", "source": "B10", "target": "B05", "contractual_monthly_exposure": 2500, "liability_share": 0.50},
        {"edge_id": "E02", "super_mechanism": "joint_liability", "specific_mechanism": "peripheral_spark_to_conduit", "source": "B10", "target": "B06", "contractual_monthly_exposure": 2500, "liability_share": 0.50},
        # B05 is the structural bottleneck and branches into the core.
        {"edge_id": "E03", "super_mechanism": "joint_liability", "specific_mechanism": "core_branch_west", "source": "B05", "target": "B01", "contractual_monthly_exposure": 2300, "liability_share": 0.50},
        {"edge_id": "E04", "super_mechanism": "joint_liability", "specific_mechanism": "core_branch_central", "source": "B05", "target": "B02", "contractual_monthly_exposure": 2300, "liability_share": 0.50},
        {"edge_id": "E05", "super_mechanism": "joint_liability", "specific_mechanism": "core_branch_east", "source": "B05", "target": "B03", "contractual_monthly_exposure": 2300, "liability_share": 0.50},
        {"edge_id": "E06", "super_mechanism": "joint_liability", "specific_mechanism": "secondary_branch", "source": "B01", "target": "B04", "contractual_monthly_exposure": 2000, "liability_share": 0.45},
        {"edge_id": "E07", "super_mechanism": "joint_liability", "specific_mechanism": "secondary_branch", "source": "B01", "target": "B11", "contractual_monthly_exposure": 2000, "liability_share": 0.45},
        {"edge_id": "E08", "super_mechanism": "joint_liability", "specific_mechanism": "secondary_branch", "source": "B02", "target": "B07", "contractual_monthly_exposure": 2000, "liability_share": 0.45},
        {"edge_id": "E09", "super_mechanism": "joint_liability", "specific_mechanism": "secondary_branch", "source": "B02", "target": "B08", "contractual_monthly_exposure": 2000, "liability_share": 0.45},
        {"edge_id": "E10", "super_mechanism": "joint_liability", "specific_mechanism": "secondary_branch", "source": "B03", "target": "B09", "contractual_monthly_exposure": 2000, "liability_share": 0.45},
        {"edge_id": "E11", "super_mechanism": "joint_liability", "specific_mechanism": "secondary_branch", "source": "B03", "target": "B12", "contractual_monthly_exposure": 2000, "liability_share": 0.45},
        {"edge_id": "E12", "super_mechanism": "joint_liability", "specific_mechanism": "terminal_branch", "source": "B04", "target": "B13", "contractual_monthly_exposure": 1800, "liability_share": 0.40},
        {"edge_id": "E13", "super_mechanism": "joint_liability", "specific_mechanism": "terminal_branch", "source": "B07", "target": "B14", "contractual_monthly_exposure": 1800, "liability_share": 0.40},
        # Non-cash and common-exposure links make the canvas mechanically varied.
        {"edge_id": "E14", "super_mechanism": "formal_group", "specific_mechanism": "center_discipline", "source": "B05", "target": "B04", "metadata": {"group_id": "G1"}},
        {"edge_id": "E15", "super_mechanism": "formal_group", "specific_mechanism": "center_discipline", "source": "B02", "target": "B11", "metadata": {"group_id": "G1"}},
        {"edge_id": "E16", "super_mechanism": "economic_exposure", "specific_mechanism": "shared_market", "source": "B01", "target": "B12", "economic_source_type": "market", "economic_source_id": "M1", "metadata": {"exposure_fraction": 0.55}},
        {"edge_id": "E17", "super_mechanism": "geographic_exposure", "specific_mechanism": "flood_zone", "source": "B07", "target": "B14", "metadata": {"location_id": "L1"}},
        # Quantified market dependencies make the M1 scenario a second cascade story.
        {"edge_id": "E18", "super_mechanism": "economic_exposure", "specific_mechanism": "dairy_market_dependency", "source": "B13", "target": "B05", "economic_source_type": "market", "economic_source_id": "M1", "metadata": {"exposure_fraction": 0.60}},
        {"edge_id": "E19", "super_mechanism": "economic_exposure", "specific_mechanism": "dairy_market_dependency", "source": "B14", "target": "B06", "economic_source_type": "market", "economic_source_id": "M1", "metadata": {"exposure_fraction": 0.55}},
        # The satellite remains visually networked while its buffers contain shocks.
        {"edge_id": "E20", "super_mechanism": "joint_liability", "specific_mechanism": "resilient_cooperative_link", "source": "B15", "target": "B16", "contractual_monthly_exposure": 1800, "liability_share": 0.25},
        {"edge_id": "E21", "super_mechanism": "formal_group", "specific_mechanism": "resilient_group_discipline", "source": "B16", "target": "B17", "metadata": {"group_id": "G4"}},
        {"edge_id": "E22", "super_mechanism": "joint_liability", "specific_mechanism": "resilient_cooperative_link", "source": "B17", "target": "B18", "contractual_monthly_exposure": 1500, "liability_share": 0.20},
        {"edge_id": "E23", "super_mechanism": "economic_exposure", "specific_mechanism": "coastal_market_dependency", "source": "B15", "target": "B18", "economic_source_type": "market", "economic_source_id": "M2", "metadata": {"exposure_fraction": 0.20}},
    ]

    return borrowers, relationships
