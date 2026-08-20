from __future__ import annotations

import numpy as np
import pandas as pd

from backend.routers.sectors import _sector_contract_fields
from engines.participant.sector_rotation_intelligence_engine import (
    SectorRotationIntelligenceEngine,
    _cross_sectional_score,
    _rolling_return,
)


def test_cross_sectional_score_preserves_missing_values() -> None:
    result = _cross_sectional_score(pd.Series([1.0, np.nan, -1.0]))
    assert result.iloc[1] != result.iloc[1]
    assert result.iloc[0] > result.iloc[2]


def test_rolling_return_is_compounded_and_requires_complete_window() -> None:
    result = _rolling_return(pd.Series([1.0, 2.0, np.nan, 4.0]), 2)
    assert pd.isna(result.iloc[0])
    assert round(float(result.iloc[1]), 6) == 3.02
    assert pd.isna(result.iloc[2])
    assert pd.isna(result.iloc[3])


def test_breadth_does_not_convert_missing_constituents_to_unchanged() -> None:
    prices = pd.DataFrame(
        [[100.0, 100.0, 100.0], [101.0, np.nan, 99.0]],
        index=["2026-08-19", "2026-08-20"],
        columns=["A", "B", "C"],
    )
    result = SectorRotationIntelligenceEngine._breadth(
        prices, {"A": "ALPHA", "B": "ALPHA", "C": "ALPHA"}, "ALPHA", 3
    )
    assert result["breadth_1d_expected"] == 3
    assert result["breadth_1d_usable"] == 2
    assert result["breadth_1d_coverage_pct"] == round(2 / 3 * 100, 2)
    assert result["breadth_1d_positive_pct"] == 50.0


def test_persistence_requires_multiple_observations() -> None:
    history = pd.DataFrame(
        {
            "sector": ["ALPHA", "ALPHA", "ALPHA", "BETA", "BETA", "BETA"],
            "date": ["1", "2", "3", "1", "2", "3"],
            "relative_strength_rank_5d": [1.0, 1.0, 1.0, 2.0, 2.0, 2.0],
        }
    )
    state, observations, rate = SectorRotationIntelligenceEngine._persistence_state(
        history, "ALPHA", 2
    )
    assert state == "PERSISTENT_LEADER"
    assert observations == 3
    assert rate == 100.0


def test_provider_contract_fields_are_additive_and_scope_institutional_context() -> (
    None
):
    fields = _sector_contract_fields(
        pd.Series(
            {
                "sector": "ALPHA",
                "date": "2026-08-20",
                "last_date": "2026-08-20",
                "contract_version": "sector-rotation-1.1",
                "institutional_context_scope": "MARKET_LEVEL_CONTEXT_ONLY",
                "evidence_quality": "MEDIUM",
                "breadth_5d_positive_pct": 60.0,
                "breadth_5d_expected": 10,
                "breadth_5d_usable": 9,
                "breadth_5d_coverage_pct": 90.0,
                "relative_return_5d": 2.0,
                "leadership_state": "IMPROVING",
                "rotation_state": "IMPROVING",
                "limitations_json": '["limited history"]',
            }
        )
    )
    assert fields["contract_version"] == "sector-rotation-1.1"
    assert fields["institutional_context"]["scope"] == "MARKET_LEVEL_CONTEXT_ONLY"
    assert fields["breadth"]["coverage_pct"] == 90.0
    assert fields["limitations"] == ["limited history"]
