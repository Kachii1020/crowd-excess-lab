"""Explainable baseline model for community heat residuals."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, Field

FEATURE_NAMES = (
    "contract_log_magnitude",
    "prior_abnormal_return",
    "prior_volatility",
    "log_market_cap",
    "market_return",
    "after_hours",
)


class BaselineEvent(BaseModel):
    heat_score: float
    contract_log_magnitude: float = Field(ge=0)
    prior_abnormal_return: float
    prior_volatility: float = Field(ge=0)
    log_market_cap: float
    market_return: float
    after_hours: bool


class CrowdExcessBaseline(BaseModel):
    feature_names: tuple[str, ...] = FEATURE_NAMES
    intercept: float
    coefficients: tuple[float, ...]
    training_rows: int = Field(ge=1)
    matrix_rank: int = Field(ge=1)
    condition_number: float = Field(ge=0)

    def predict(self, event: BaselineEvent) -> float:
        values = _feature_values(event)
        return self.intercept + sum(
            coefficient * value
            for coefficient, value in zip(self.coefficients, values, strict=True)
        )


class CrowdExcessResult(BaseModel):
    actual_heat: float
    predicted_normal_heat: float
    crowd_excess: float


def _feature_values(event: BaselineEvent) -> tuple[float, ...]:
    values = (
        event.contract_log_magnitude,
        event.prior_abnormal_return,
        event.prior_volatility,
        event.log_market_cap,
        event.market_return,
        float(event.after_hours),
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("baseline features must be finite")
    return values


def fit_baseline(events: Sequence[BaselineEvent]) -> CrowdExcessBaseline:
    minimum_rows = len(FEATURE_NAMES) + 2
    if len(events) < minimum_rows:
        raise ValueError(f"at least {minimum_rows} historical events are required")

    features = np.asarray([_feature_values(event) for event in events], dtype=float)
    target = np.asarray([event.heat_score for event in events], dtype=float)
    if not np.isfinite(target).all():
        raise ValueError("heat scores must be finite")
    design = np.column_stack([np.ones(len(events)), features])
    coefficients, _, matrix_rank, singular_values = np.linalg.lstsq(design, target, rcond=None)
    smallest = float(np.min(singular_values))
    condition_number = float(np.max(singular_values) / smallest) if smallest > 0 else float("inf")
    return CrowdExcessBaseline(
        intercept=float(coefficients[0]),
        coefficients=tuple(float(value) for value in coefficients[1:]),
        training_rows=len(events),
        matrix_rank=int(matrix_rank),
        condition_number=condition_number,
    )


def score_event(model: CrowdExcessBaseline, event: BaselineEvent) -> CrowdExcessResult:
    predicted = model.predict(event)
    return CrowdExcessResult(
        actual_heat=event.heat_score,
        predicted_normal_heat=predicted,
        crowd_excess=event.heat_score - predicted,
    )
