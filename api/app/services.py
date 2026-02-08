"""Service layer: convert GraphQL inputs to pricing library objects and run pricing/risk."""

from __future__ import annotations

from typing import Optional

from pricing.curves import HazardRateCurve, ZeroRateCurve
from pricing.market import Market
from pricing.pricing import price
from pricing.products.bond import ZeroCouponBond
from pricing.products.cds import CDS
from pricing.products.fx import FXForward
from pricing.products.mortgage import LevelPayMortgage
from pricing.products.swap import FixedFloatSwap
from pricing.risk import cs01_parallel
from pricing.risk import fx_delta as risk_fx_delta
from pricing.risk import pv01_parallel

from app.types import (
    CDSInput,
    CurveInput,
    FXForwardInput,
    FixedFloatSwapInput,
    HazardCurveInput,
    MarketInput,
    MortgageInput,
    PricingResult,
    RiskMeasures,
    ZeroCouponBondInput,
)


def _curve_from_input(c: CurveInput) -> ZeroRateCurve:
    """Build ZeroRateCurve from GraphQL CurveInput."""
    return ZeroRateCurve(
        name=c.name,
        pillars=list(c.pillars),
        zero_rates_cc=list(c.zero_rates_cc),
        t0=c.t0,
    )


def _hazard_curve_from_input(h: HazardCurveInput) -> HazardRateCurve:
    """Build HazardRateCurve from GraphQL HazardCurveInput."""
    return HazardRateCurve(
        name=h.name,
        pillars=list(h.pillars),
        hazard_rates=list(h.hazard_rates),
        t0=h.t0,
    )


def market_from_input(m: MarketInput) -> Market:
    """Build Market from GraphQL MarketInput."""
    if not m.curves:
        raise ValueError("market.curves must not be empty")
    curves: dict[str, ZeroRateCurve | HazardRateCurve] = {}
    for c in m.curves:
        curves[c.name] = _curve_from_input(c)
    if m.hazard_curves:
        for h in m.hazard_curves:
            curves[h.name] = _hazard_curve_from_input(h)
    fx_spot: dict[str, float] = {}
    if m.fx_spot:
        for fx in m.fx_spot:
            fx_spot[fx.pair] = fx.spot
    return Market(curves=curves, fx_spot=fx_spot)


def _validate_curve_in_market(market: Market, curve_name: str, context: str) -> None:
    if curve_name not in market.curves:
        raise ValueError(
            f"{context}: curve '{curve_name}' not found in market. "
            f"Available curves: {list(market.curves.keys())}"
        )


def price_zero_coupon_bond(
    bond: ZeroCouponBondInput,
    market: MarketInput,
    calculate_pv01: bool = False,
    pv01_curve_name: Optional[str] = None,
    pv01_bump_bp: float = 1.0,
) -> PricingResult:
    """Price a zero-coupon bond and optionally compute PV01."""
    if bond.maturity < 0:
        raise ValueError("bond.maturity must be >= 0")
    m = market_from_input(market)
    _validate_curve_in_market(m, bond.curve, "ZeroCouponBond")
    instrument = ZeroCouponBond(
        curve=bond.curve,
        maturity=bond.maturity,
        notional=bond.notional,
    )
    npv = price(instrument, m)
    risk_measures = None
    if calculate_pv01:
        curve_name = pv01_curve_name or bond.curve
        _validate_curve_in_market(m, curve_name, "PV01")
        pv01 = pv01_parallel(instrument, m, curve_name, bump_bp=pv01_bump_bp)
        risk_measures = RiskMeasures(pv01=pv01, fx_delta=None)
    return PricingResult(npv=npv, risk_measures=risk_measures)


def price_swap(
    swap: FixedFloatSwapInput,
    market: MarketInput,
    calculate_pv01: bool = False,
    pv01_curve_name: Optional[str] = None,
    pv01_bump_bp: float = 1.0,
) -> PricingResult:
    """Price a fixed-float swap and optionally compute PV01."""
    if not swap.pay_times:
        raise ValueError("swap.pay_times must not be empty")
    m = market_from_input(market)
    _validate_curve_in_market(m, swap.curve, "FixedFloatSwap")
    instrument = FixedFloatSwap(
        curve=swap.curve,
        notional=swap.notional,
        fixed_rate=swap.fixed_rate,
        pay_times=list(swap.pay_times),
        t0=swap.t0,
    )
    npv = price(instrument, m)
    risk_measures = None
    if calculate_pv01:
        curve_name = pv01_curve_name or swap.curve
        _validate_curve_in_market(m, curve_name, "PV01")
        pv01 = pv01_parallel(instrument, m, curve_name, bump_bp=pv01_bump_bp)
        risk_measures = RiskMeasures(pv01=pv01, fx_delta=None)
    return PricingResult(npv=npv, risk_measures=risk_measures)


def price_fx_forward(
    forward: FXForwardInput,
    market: MarketInput,
    calculate_pv01: bool = False,
    calculate_fx_delta: bool = False,
    pv01_curve_name: Optional[str] = None,
    pv01_bump_bp: float = 1.0,
    fx_delta_pair: Optional[str] = None,
    fx_delta_bump_pct: float = 0.01,
) -> PricingResult:
    """Price an FX forward (CIP) and optionally compute PV01 and FX delta."""
    if forward.maturity < 0:
        raise ValueError("forward.maturity must be >= 0")
    m = market_from_input(market)
    _validate_curve_in_market(m, forward.base_curve, "FXForward base_curve")
    _validate_curve_in_market(m, forward.quote_curve, "FXForward quote_curve")
    if forward.pair not in m.fx_spot:
        raise ValueError(
            f"FXForward: FX pair '{forward.pair}' not found in market. "
            f"Available pairs: {list(m.fx_spot.keys())}"
        )
    instrument = FXForward(
        pair=forward.pair,
        base_curve=forward.base_curve,
        quote_curve=forward.quote_curve,
        maturity=forward.maturity,
        notional_base=forward.notional_base,
        strike=forward.strike,
    )
    npv = price(instrument, m)
    pv01_val = None
    fx_delta_val = None
    if calculate_pv01:
        curve_name = pv01_curve_name or forward.quote_curve
        _validate_curve_in_market(m, curve_name, "PV01")
        pv01_val = pv01_parallel(instrument, m, curve_name, bump_bp=pv01_bump_bp)
    if calculate_fx_delta:
        pair = fx_delta_pair or forward.pair
        if pair not in m.fx_spot:
            raise ValueError(
                f"FX delta: pair '{pair}' not found in market. "
                f"Available pairs: {list(m.fx_spot.keys())}"
            )
        fx_delta_val = risk_fx_delta(instrument, m, pair, bump_pct=fx_delta_bump_pct)
    if pv01_val is not None or fx_delta_val is not None:
        risk_measures = RiskMeasures(pv01=pv01_val, fx_delta=fx_delta_val)
    else:
        risk_measures = None
    return PricingResult(npv=npv, risk_measures=risk_measures)


def price_mortgage(
    mortgage: MortgageInput,
    market: MarketInput,
    calculate_pv01: bool = False,
    pv01_curve_name: Optional[str] = None,
    pv01_bump_bp: float = 1.0,
) -> PricingResult:
    """Price a level-pay mortgage and optionally compute PV01."""
    if mortgage.term_years <= 0 or mortgage.payments_per_year <= 0:
        raise ValueError("term_years and payments_per_year must be positive")
    m = market_from_input(market)
    _validate_curve_in_market(m, mortgage.curve, "LevelPayMortgage")
    instrument = LevelPayMortgage(
        curve=mortgage.curve,
        notional=mortgage.notional,
        annual_rate=mortgage.annual_rate,
        term_years=mortgage.term_years,
        payments_per_year=mortgage.payments_per_year,
    )
    npv = price(instrument, m)
    risk_measures = None
    if calculate_pv01:
        curve_name = pv01_curve_name or mortgage.curve
        _validate_curve_in_market(m, curve_name, "PV01")
        pv01 = pv01_parallel(instrument, m, curve_name, bump_bp=pv01_bump_bp)
        risk_measures = RiskMeasures(pv01=pv01, fx_delta=None)
    return PricingResult(npv=npv, risk_measures=risk_measures)


def price_cds(
    cds: CDSInput,
    market: MarketInput,
    calculate_cs01: bool = False,
    cs01_hazard_curve_name: Optional[str] = None,
    cs01_bump_bp: float = 1.0,
) -> PricingResult:
    """Price a single-name CDS and optionally compute CS01."""
    if not cds.pay_times:
        raise ValueError("cds.pay_times must not be empty")
    m = market_from_input(market)
    _validate_curve_in_market(m, cds.discount_curve, "CDS discount_curve")
    _validate_curve_in_market(m, cds.survival_curve, "CDS survival_curve")
    instrument = CDS(
        discount_curve=cds.discount_curve,
        survival_curve=cds.survival_curve,
        notional=cds.notional,
        premium_rate=cds.premium_rate,
        pay_times=list(cds.pay_times),
        recovery=cds.recovery,
        t0=cds.t0,
        protection_buyer=cds.protection_buyer,
    )
    npv = price(instrument, m)
    risk_measures = None
    if calculate_cs01:
        hazard_curve_name = cs01_hazard_curve_name or cds.survival_curve
        _validate_curve_in_market(m, hazard_curve_name, "CS01")
        cs01_val = cs01_parallel(
            instrument, m, hazard_curve_name, bump_bp=cs01_bump_bp
        )
        risk_measures = RiskMeasures(pv01=None, fx_delta=None, cs01=cs01_val)
    return PricingResult(npv=npv, risk_measures=risk_measures)
