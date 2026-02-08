"""Tests for ZeroCouponBond."""

import math

from pricing.curves import ZeroRateCurve
from pricing.market import Market
from pricing.products.bond import ZeroCouponBond
from pricing.pricing import price


def test_bond_pv_equals_notional_times_df() -> None:
    """Bond PV = notional * DF(maturity)."""
    curve = ZeroRateCurve(name="C", pillars=[1.0, 2.0], zero_rates_cc=[0.04, 0.035])
    market = Market(curves={"C": curve})
    notional = 1_000_000
    maturity = 1.5
    bond = ZeroCouponBond(curve="C", maturity=maturity, notional=notional)
    pv = price(bond, market)
    expected = notional * curve.df(maturity)
    assert abs(pv - expected) < 1e-6


def test_bond_at_pillar() -> None:
    """Bond at exact pillar: PV = notional * exp(-r*T)."""
    r = 0.05
    T = 2.0
    curve = ZeroRateCurve(name="C", pillars=[T], zero_rates_cc=[r])
    market = Market(curves={"C": curve})
    bond = ZeroCouponBond(curve="C", maturity=T, notional=100.0)
    pv = price(bond, market)
    assert abs(pv - 100.0 * math.exp(-r * T)) < 1e-10
