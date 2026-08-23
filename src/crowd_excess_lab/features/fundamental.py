"""Objective magnitude for single sales/supply contract disclosures."""

from __future__ import annotations

import math
from decimal import Decimal

from pydantic import BaseModel, Field


class SupplyContractShock(BaseModel):
    contract_amount_krw: Decimal = Field(ge=0)
    annual_revenue_krw: Decimal = Field(gt=0)
    contract_to_revenue_ratio: float = Field(ge=0)
    contract_to_revenue_percent: float = Field(ge=0)
    log_scaled_magnitude: float = Field(ge=0)


def compute_supply_contract_shock(
    contract_amount_krw: Decimal | int | str,
    annual_revenue_krw: Decimal | int | str,
) -> SupplyContractShock:
    contract_amount = Decimal(contract_amount_krw)
    annual_revenue = Decimal(annual_revenue_krw)
    if contract_amount < 0:
        raise ValueError("contract_amount_krw must not be negative")
    if annual_revenue <= 0:
        raise ValueError("annual_revenue_krw must be positive")

    ratio = float(contract_amount / annual_revenue)
    return SupplyContractShock(
        contract_amount_krw=contract_amount,
        annual_revenue_krw=annual_revenue,
        contract_to_revenue_ratio=ratio,
        contract_to_revenue_percent=ratio * 100,
        log_scaled_magnitude=math.log1p(ratio),
    )
