"""Tests for LevelPayMortgage."""

import math

from pricing.curves import ZeroRateCurve
from pricing.market import Market
from pricing.products.mortgage import LevelPayMortgage
from pricing.pricing import price


def test_mortgage_pv_at_par() -> None:
    """When discount curve equals mortgage rate, PV of level payments ≈ notional."""
    rate = 0.04
    curve = ZeroRateCurve(
        name="C",
        pillars=[0.5, 1.0, 1.5, 2.0],
        zero_rates_cc=[rate] * 4,
    )
    market = Market(curves={"C": curve})
    notional = 1_000_000
    mortgage = LevelPayMortgage(
        curve="C",
        notional=notional,
        annual_rate=rate,
        term_years=2.0,
        payments_per_year=1,
    )
    pv = price(mortgage, market)
    # Level payment uses periodic rate; discount curve uses continuous. PV close to notional.
    assert abs(pv - notional) < notional * 0.005


def test_mortgage_pv_positive_when_curve_below_rate() -> None:
    """When discount rate < mortgage rate, PV > notional (lender receives more in PV terms)."""
    curve = ZeroRateCurve(
        name="C",
        pillars=[1.0, 5.0],
        zero_rates_cc=[0.04, 0.04],
    )
    market = Market(curves={"C": curve})
    notional = 100_000
    mortgage = LevelPayMortgage(
        curve="C",
        notional=notional,
        annual_rate=0.06,
        term_years=2.0,
        payments_per_year=2,
    )
    pv = price(mortgage, market)
    assert pv > notional


def test_mortgage_payment_times() -> None:
    """1Y term, 2 payments per year: pay_times 0.5, 1.0; PV = payment * (DF(0.5) + DF(1.0))."""
    curve = ZeroRateCurve(name="C", pillars=[0.5, 1.0], zero_rates_cc=[0.05, 0.05])
    market = Market(curves={"C": curve})
    notional = 1000.0
    r = 0.05 / 2  # semi-annual
    n = 2
    payment = notional * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    mortgage = LevelPayMortgage(
        curve="C",
        notional=notional,
        annual_rate=0.05,
        term_years=1.0,
        payments_per_year=2,
    )
    pv = price(mortgage, market)
    df_05 = math.exp(-0.05 * 0.5)
    df_10 = math.exp(-0.05 * 1.0)
    expected = payment * (df_05 + df_10)
    assert abs(pv - expected) < 0.01
