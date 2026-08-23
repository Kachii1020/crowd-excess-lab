"""Auditable community-window aggregation and preregistered heat score."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, Field, model_validator

from crowd_excess_lab.models import CommunityObservation


class CommunityWindowMetrics(BaseModel):
    post_count: int = Field(ge=0)
    unique_authors: int = Field(ge=0)
    mean_sentiment: float = Field(ge=-1, le=1)
    sentiment_extremity: float = Field(ge=0, le=1)
    disagreement: float = Field(ge=0)
    mean_engagement: float = Field(ge=0)
    duplicate_ratio: float = Field(ge=0, le=1)


class HeatWeights(BaseModel):
    activity: float = Field(default=0.35, ge=0)
    participation: float = Field(default=0.20, ge=0)
    sentiment_extremity: float = Field(default=0.20, ge=0)
    disagreement: float = Field(default=0.15, ge=0)
    engagement: float = Field(default=0.10, ge=0)
    duplicate_penalty: float = Field(default=0.25, ge=0)

    @model_validator(mode="after")
    def directional_weights_sum_to_one(self) -> HeatWeights:
        component_sum = (
            self.activity
            + self.participation
            + self.sentiment_extremity
            + self.disagreement
            + self.engagement
        )
        if not math.isclose(component_sum, 1.0, abs_tol=1e-9):
            raise ValueError("non-penalty heat weights must sum to 1")
        return self


class CommunityHeat(BaseModel):
    activity_z: float
    participation_z: float
    sentiment_extremity_z: float
    disagreement_z: float
    engagement_z: float
    duplicate_penalty: float = Field(ge=0)
    heat_score: float
    weights: HeatWeights


def aggregate_community_window(
    observations: Sequence[CommunityObservation],
) -> CommunityWindowMetrics:
    if not observations:
        return CommunityWindowMetrics(
            post_count=0,
            unique_authors=0,
            mean_sentiment=0,
            sentiment_extremity=0,
            disagreement=0,
            mean_engagement=0,
            duplicate_ratio=0,
        )

    sentiments = np.asarray([item.sentiment_score for item in observations], dtype=float)
    extremities = np.asarray([item.emotion_intensity for item in observations], dtype=float)
    engagement = np.asarray(
        [math.log1p(item.reply_count + item.like_count) for item in observations],
        dtype=float,
    )
    duplicate_count = sum(item.is_duplicate for item in observations)
    return CommunityWindowMetrics(
        post_count=len(observations),
        unique_authors=len({item.author_hash for item in observations}),
        mean_sentiment=float(np.mean(sentiments)),
        sentiment_extremity=float(np.mean(extremities)),
        disagreement=float(np.std(sentiments, ddof=0)),
        mean_engagement=float(np.mean(engagement)),
        duplicate_ratio=duplicate_count / len(observations),
    )


def robust_zscore(value: float, baseline: Sequence[float], *, cap: float = 5.0) -> float:
    if not baseline:
        raise ValueError("a non-empty baseline is required")
    values = np.asarray(baseline, dtype=float)
    if not np.isfinite(values).all() or not math.isfinite(value):
        raise ValueError("z-score inputs must be finite")
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad > 0:
        score = (value - median) / (1.4826 * mad)
    else:
        standard_deviation = float(np.std(values, ddof=0))
        if standard_deviation > 0:
            score = (value - median) / standard_deviation
        elif math.isclose(value, median):
            score = 0.0
        else:
            score = math.copysign(cap, value - median)
    return float(np.clip(score, -cap, cap))


def compute_community_heat(
    event_window: CommunityWindowMetrics,
    baseline_windows: Sequence[CommunityWindowMetrics],
    *,
    weights: HeatWeights | None = None,
) -> CommunityHeat:
    if len(baseline_windows) < 5:
        raise ValueError("at least five prior baseline windows are required")
    chosen_weights = weights or HeatWeights()

    activity_z = robust_zscore(
        event_window.post_count, [item.post_count for item in baseline_windows]
    )
    participation_z = robust_zscore(
        event_window.unique_authors, [item.unique_authors for item in baseline_windows]
    )
    extremity_z = robust_zscore(
        event_window.sentiment_extremity,
        [item.sentiment_extremity for item in baseline_windows],
    )
    disagreement_z = robust_zscore(
        event_window.disagreement, [item.disagreement for item in baseline_windows]
    )
    engagement_z = robust_zscore(
        event_window.mean_engagement, [item.mean_engagement for item in baseline_windows]
    )
    duplicate_penalty = chosen_weights.duplicate_penalty * event_window.duplicate_ratio
    heat_score = (
        chosen_weights.activity * activity_z
        + chosen_weights.participation * participation_z
        + chosen_weights.sentiment_extremity * extremity_z
        + chosen_weights.disagreement * disagreement_z
        + chosen_weights.engagement * engagement_z
        - duplicate_penalty
    )
    return CommunityHeat(
        activity_z=activity_z,
        participation_z=participation_z,
        sentiment_extremity_z=extremity_z,
        disagreement_z=disagreement_z,
        engagement_z=engagement_z,
        duplicate_penalty=duplicate_penalty,
        heat_score=heat_score,
        weights=chosen_weights,
    )
