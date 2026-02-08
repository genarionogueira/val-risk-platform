"""Tests for ZeroRateCurve."""

import math
import pytest

from pricing.curves import ZeroRateCurve


def test_curve_interpolation_endpoints() -> None:
    """Endpoints: rate at first/last pillar equals stored rate."""
    pillars = [0.5, 1.0, 2.0, 5.0]
    rates = [0.05, 0.04, 0.035, 0.03]
    curve = ZeroRateCurve(name="C", pillars=pillars, zero_rates_cc=rates)
    assert curve.zero_rate_cc(0.5) == 0.05
    assert curve.zero_rate_cc(5.0) == 0.03


def test_curve_interpolation_midpoint() -> None:
    """Midpoint: linear interp between two pillars."""
    pillars = [0.0, 2.0]
    rates = [0.04, 0.06]
    curve = ZeroRateCurve(name="C", pillars=pillars, zero_rates_cc=rates)
    # at t=1.0: r = 0.04 + (0.06-0.04)*1/2 = 0.05
    assert abs(curve.zero_rate_cc(1.0) - 0.05) < 1e-10


def test_curve_before_first_pillar() -> None:
    """Before first pillar: flat at first rate."""
    pillars = [0.5, 1.0]
    rates = [0.05, 0.04]
    curve = ZeroRateCurve(name="C", pillars=pillars, zero_rates_cc=rates)
    assert curve.zero_rate_cc(0.0) == 0.05
    assert curve.zero_rate_cc(0.25) == 0.05


def test_curve_after_last_pillar() -> None:
    """After last pillar: flat at last rate."""
    pillars = [0.5, 1.0]
    rates = [0.05, 0.04]
    curve = ZeroRateCurve(name="C", pillars=pillars, zero_rates_cc=rates)
    assert curve.zero_rate_cc(2.0) == 0.04


def test_df_monotonic_decreasing_positive_rates() -> None:
    """DF is monotonic decreasing when rates are positive."""
    pillars = [0.5, 1.0, 2.0, 5.0]
    rates = [0.05, 0.04, 0.035, 0.03]
    curve = ZeroRateCurve(name="C", pillars=pillars, zero_rates_cc=rates)
    times = [0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0]
    dfs = [curve.df(t) for t in times]
    for i in range(1, len(dfs)):
        assert dfs[i] < dfs[i - 1]
    assert all(0 < d <= 1 for d in dfs)


def test_df_formula() -> None:
    """DF(t) = exp(-r(t)*t)."""
    pillars = [1.0]
    rates = [0.05]
    curve = ZeroRateCurve(name="C", pillars=pillars, zero_rates_cc=rates)
    assert abs(curve.df(1.0) - math.exp(-0.05)) < 1e-10


def test_bumped_curve() -> None:
    """Bumped curve has rates shifted by bump."""
    curve = ZeroRateCurve(name="C", pillars=[1.0], zero_rates_cc=[0.04])
    bumped = curve.bumped(0.01)
    assert abs(bumped.zero_rate_cc(1.0) - 0.05) < 1e-10
    assert abs(bumped.df(1.0) - math.exp(-0.05)) < 1e-10


def test_validate_pillars_strictly_increasing() -> None:
    """Validation: pillars must be strictly increasing."""
    with pytest.raises(ValueError, match="strictly increasing"):
        ZeroRateCurve(name="C", pillars=[1.0, 1.0], zero_rates_cc=[0.04, 0.04])
    with pytest.raises(ValueError, match="strictly increasing"):
        ZeroRateCurve(name="C", pillars=[2.0, 1.0], zero_rates_cc=[0.04, 0.04])


def test_validate_same_length() -> None:
    """Validation: pillars and rates same length."""
    with pytest.raises(ValueError, match="same length"):
        ZeroRateCurve(name="C", pillars=[1.0, 2.0], zero_rates_cc=[0.04])


def test_zero_rate_t_negative_raises() -> None:
    """zero_rate_cc(t) with t < 0 raises."""
    curve = ZeroRateCurve(name="C", pillars=[1.0], zero_rates_cc=[0.04])
    with pytest.raises(ValueError, match="t must be >= 0"):
        curve.zero_rate_cc(-0.1)
