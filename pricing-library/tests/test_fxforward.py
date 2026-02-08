"""Tests for FXForward (CIP-based)."""

import math

from pricing.curves import ZeroRateCurve
from pricing.market import Market
from pricing.products.fx import FXForward
from pricing.pricing import price


def test_fx_forward_pv_formula_cip() -> None:
    """PV = notional_base * DF_quote * (F - strike) with F = spot * DF_base/DF_quote."""
    # Same curve for base and quote => F = spot (CIP collapses to spot when rates equal)
    curve = ZeroRateCurve(name="USD", pillars=[1.0], zero_rates_cc=[0.05])
    market = Market(curves={"USD": curve}, fx_spot={"EURUSD": 1.10})
    notional_base = 1_000_000
    maturity = 1.0
    strike = 1.08
    fwd = FXForward(
        pair="EURUSD",
        base_curve="USD",
        quote_curve="USD",
        maturity=maturity,
        notional_base=notional_base,
        strike=strike,
    )
    pv = price(fwd, market)
    df = math.exp(-0.05 * maturity)
    fwd_rate = 1.10 * df / df  # = spot when base=quote
    expected = notional_base * df * (fwd_rate - strike)
    assert abs(pv - expected) < 1e-6


def test_fx_forward_cip_with_distinct_curves() -> None:
    """CIP: F = spot * DF_base/DF_quote; when base rates < quote rates, F > spot."""
    eur = ZeroRateCurve(name="EUR", pillars=[1.0], zero_rates_cc=[0.03])
    usd = ZeroRateCurve(name="USD", pillars=[1.0], zero_rates_cc=[0.05])
    market = Market(curves={"EUR": eur, "USD": usd}, fx_spot={"EURUSD": 1.08})
    fwd = FXForward(
        pair="EURUSD",
        base_curve="EUR",
        quote_curve="USD",
        maturity=1.0,
        notional_base=1_000_000,
        strike=1.08,
    )
    pv = price(fwd, market)
    df_eur = math.exp(-0.03 * 1.0)
    df_usd = math.exp(-0.05 * 1.0)
    fwd_rate = 1.08 * df_eur / df_usd  # > 1.08 since EUR rates lower
    expected = 1_000_000 * df_usd * (fwd_rate - 1.08)
    assert abs(pv - expected) < 1e-6
    assert pv > 0  # F > strike => positive PV for long base


def test_fx_forward_at_the_money_zero_pv() -> None:
    """When spot == strike and base=quote curve, F=spot so PV = 0."""
    curve = ZeroRateCurve(name="USD", pillars=[1.0], zero_rates_cc=[0.05])
    market = Market(curves={"USD": curve}, fx_spot={"EURUSD": 1.08})
    fwd = FXForward(
        pair="EURUSD",
        base_curve="USD",
        quote_curve="USD",
        maturity=1.0,
        notional_base=5_000_000,
        strike=1.08,
    )
    pv = price(fwd, market)
    assert abs(pv) < 1e-6
