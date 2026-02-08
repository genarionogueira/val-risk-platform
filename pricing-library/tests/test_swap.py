"""Tests for FixedFloatSwap."""

from pricing.curves import ZeroRateCurve
from pricing.market import Market
from pricing.products.swap import FixedFloatSwap
from pricing.pricing import price


def test_swap_par_fixed_near_zero() -> None:
    """When fixed_rate is close to par (flat curve), PV should be near 0."""
    # Flat curve => forwards implied from curve; at par fixed ~ float => PV small
    rate = 0.04
    curve = ZeroRateCurve(
        name="C",
        pillars=[0.5, 1.0, 1.5, 2.0],
        zero_rates_cc=[rate] * 4,
    )
    market = Market(curves={"C": curve})
    swap = FixedFloatSwap(
        curve="C",
        notional=10_000_000,
        fixed_rate=rate,
        pay_times=[0.5, 1.0, 1.5, 2.0],
    )
    pv = price(swap, market)
    # Receive float, pay fixed; at approx par, PV is small relative to notional
    assert abs(pv) < 0.01 * 10_000_000  # within 1% of notional


def test_swap_high_fixed_negative_pv() -> None:
    """If fixed rate > implied forwards, we pay more fixed => PV (float - fixed) negative."""
    curve = ZeroRateCurve(
        name="C",
        pillars=[0.5, 1.0],
        zero_rates_cc=[0.03, 0.03],
    )
    market = Market(curves={"C": curve})
    swap = FixedFloatSwap(
        curve="C",
        notional=1_000_000,
        fixed_rate=0.10,  # high fixed
        pay_times=[0.5, 1.0],
    )
    pv = price(swap, market)
    assert pv < 0


def test_swap_low_fixed_positive_pv() -> None:
    """If fixed rate < implied forwards, we receive more float => PV positive."""
    curve = ZeroRateCurve(
        name="C",
        pillars=[0.5, 1.0],
        zero_rates_cc=[0.05, 0.05],
    )
    market = Market(curves={"C": curve})
    swap = FixedFloatSwap(
        curve="C",
        notional=1_000_000,
        fixed_rate=0.01,  # low fixed
        pay_times=[0.5, 1.0],
    )
    pv = price(swap, market)
    assert pv > 0
