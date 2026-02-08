"""Tests for PV01 and FX delta."""

import math

from pricing.curves import ZeroRateCurve
from pricing.market import Market
from pricing.products.bond import ZeroCouponBond
from pricing.products.fx import FXForward
from pricing.pricing import price
from pricing.risk import pv01_parallel, fx_delta


def test_pv01_zcb_negative() -> None:
    """PV01 for ZCB: bumping rates up => DF down => PV down => PV01 negative."""
    curve = ZeroRateCurve(name="C", pillars=[1.0, 2.0], zero_rates_cc=[0.04, 0.04])
    market = Market(curves={"C": curve})
    bond = ZeroCouponBond(curve="C", maturity=1.5, notional=1_000_000)
    pv01 = pv01_parallel(bond, market, "C", bump_bp=1.0)
    assert pv01 < 0


def test_pv01_scale_sanity() -> None:
    """PV01 magnitude: 1bp bump on 2Y ~ -PV * 0.0001 * 2 for small effect."""
    curve = ZeroRateCurve(name="C", pillars=[2.0], zero_rates_cc=[0.04])
    market = Market(curves={"C": curve})
    bond = ZeroCouponBond(curve="C", maturity=2.0, notional=1_000_000)
    pv_base = price(bond, market)
    pv01 = pv01_parallel(bond, market, "C", bump_bp=1.0)
    # Approx: d(PV)/dr ~ -PV * T => d(PV) ~ -PV * T * 1e-4 for 1bp
    approx_dv01 = -pv_base * 2.0 * 0.0001
    assert abs(pv01 - approx_dv01) < abs(approx_dv01) * 0.5  # same order


def test_fx_delta_close_to_df_base_times_notional() -> None:
    """For FX forward (CIP), d(PV)/d(spot) = notional_base * DF_base => fx_delta ~ N*DF_base."""
    eur = ZeroRateCurve(name="EUR", pillars=[1.0], zero_rates_cc=[0.05])
    usd = ZeroRateCurve(name="USD", pillars=[1.0], zero_rates_cc=[0.05])
    market = Market(curves={"EUR": eur, "USD": usd}, fx_spot={"EURUSD": 1.08})
    notional_base = 5_000_000
    fwd = FXForward(
        pair="EURUSD",
        base_curve="EUR",
        quote_curve="USD",
        maturity=1.0,
        notional_base=notional_base,
        strike=1.085,
    )
    delta = fx_delta(fwd, market, "EURUSD", bump_pct=0.01)
    df_base = math.exp(-0.05 * 1.0)
    expected = notional_base * df_base
    # Allow small numerical difference
    assert abs(delta - expected) < expected * 0.01
