from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from crowd_excess_lab.features import (
    BaselineEvent,
    CommunityWindowMetrics,
    aggregate_community_window,
    compute_community_heat,
    compute_supply_contract_shock,
    fit_baseline,
    score_event,
)
from crowd_excess_lab.models import CollectionBasis, CommunityObservation


def test_supply_contract_shock_keeps_numerator_and_denominator() -> None:
    result = compute_supply_contract_shock(Decimal("5000000000"), Decimal("100000000000"))

    assert result.contract_amount_krw == Decimal("5000000000")
    assert result.annual_revenue_krw == Decimal("100000000000")
    assert result.contract_to_revenue_ratio == pytest.approx(0.05)
    assert result.contract_to_revenue_percent == pytest.approx(5.0)


def test_supply_contract_shock_rejects_zero_revenue() -> None:
    with pytest.raises(ValueError, match="positive"):
        compute_supply_contract_shock(1, 0)


def _observation(index: int, sentiment: float, duplicate: bool) -> CommunityObservation:
    posted = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index)
    return CommunityObservation(
        source="synthetic_test_only",
        post_id_hash=f"{index:064x}",
        ticker="005930",
        posted_at=posted,
        author_hash=f"{index + 100:064x}",
        sentiment_score=sentiment,
        emotion_intensity=abs(sentiment),
        is_duplicate=duplicate,
        reply_count=index,
        like_count=index * 2,
        collected_at=posted + timedelta(days=1),
        collection_basis=CollectionBasis.CONSENTED_DATASET,
    )


def test_community_aggregation_is_transparent() -> None:
    metrics = aggregate_community_window([_observation(1, 0.8, False), _observation(2, -0.2, True)])

    assert metrics.post_count == 2
    assert metrics.unique_authors == 2
    assert metrics.mean_sentiment == pytest.approx(0.3)
    assert metrics.disagreement == pytest.approx(0.5)
    assert metrics.duplicate_ratio == pytest.approx(0.5)


def test_community_heat_exposes_components_and_duplicate_penalty() -> None:
    baseline = [
        CommunityWindowMetrics(
            post_count=10,
            unique_authors=8,
            mean_sentiment=0.1,
            sentiment_extremity=0.2,
            disagreement=0.1,
            mean_engagement=0.5,
            duplicate_ratio=0.1,
        )
        for _ in range(5)
    ]
    event = CommunityWindowMetrics(
        post_count=30,
        unique_authors=20,
        mean_sentiment=0.8,
        sentiment_extremity=0.9,
        disagreement=0.4,
        mean_engagement=1.5,
        duplicate_ratio=0.4,
    )

    heat = compute_community_heat(event, baseline)

    assert heat.activity_z == 5.0
    assert heat.participation_z == 5.0
    assert heat.duplicate_penalty == pytest.approx(0.1)
    assert heat.heat_score == pytest.approx(4.9)
    assert heat.weights.activity == 0.35


def _baseline_events() -> list[BaselineEvent]:
    rng = np.random.default_rng(7)
    events: list[BaselineEvent] = []
    for index in range(30):
        features = rng.normal(size=5)
        after_hours = bool(index % 2)
        heat = (
            0.3
            + 0.8 * abs(features[0])
            + 1.2 * features[1]
            - 0.4 * abs(features[2])
            + 0.05 * features[3]
            + 0.9 * features[4]
            + 0.2 * float(after_hours)
        )
        events.append(
            BaselineEvent(
                heat_score=heat,
                contract_log_magnitude=abs(features[0]),
                prior_abnormal_return=features[1],
                prior_volatility=abs(features[2]),
                log_market_cap=20 + features[3],
                market_return=features[4],
                after_hours=after_hours,
            )
        )
    return events


def test_crowd_excess_is_actual_minus_predicted_normal_heat() -> None:
    model = fit_baseline(_baseline_events())
    event = BaselineEvent(
        heat_score=5.0,
        contract_log_magnitude=0.08,
        prior_abnormal_return=0.01,
        prior_volatility=0.02,
        log_market_cap=22,
        market_return=0.003,
        after_hours=False,
    )

    result = score_event(model, event)

    assert result.crowd_excess == pytest.approx(result.actual_heat - result.predicted_normal_heat)
    assert model.training_rows == 30
    assert model.feature_names[0] == "contract_log_magnitude"


def test_baseline_rejects_too_few_events() -> None:
    with pytest.raises(ValueError, match="at least 8"):
        fit_baseline(_baseline_events()[:7])
