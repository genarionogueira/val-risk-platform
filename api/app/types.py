"""GraphQL types for pricing and risk API."""

from __future__ import annotations

from typing import Optional

import strawberry


# --- Input types (request payloads) ---


@strawberry.input
class CurveInput:
    """Curve definition: name, pillars (year fractions), zero rates (continuously compounded)."""

    name: str
    pillars: list[float]
    zero_rates_cc: list[float]
    t0: float = 0.0


@strawberry.input
class FxSpotInput:
    """FX spot rate for a pair (e.g. EURUSD)."""

    pair: str
    spot: float


@strawberry.input
class HazardCurveInput:
    """Hazard/survival curve: df(t) returns S(t)."""

    name: str
    pillars: list[float]
    hazard_rates: list[float]
    t0: float = 0.0


@strawberry.input
class MarketInput:
    """Market snapshot: curves, hazard curves, and FX spots."""

    curves: list[CurveInput]
    hazard_curves: Optional[list[HazardCurveInput]] = None
    fx_spot: Optional[list[FxSpotInput]] = None


@strawberry.input
class ZeroCouponBondInput:
    """Zero-coupon bond: single cashflow at maturity."""

    curve: str
    maturity: float
    notional: float


@strawberry.input
class FixedFloatSwapInput:
    """Fixed-float interest rate swap (receive float, pay fixed)."""

    curve: str
    notional: float
    fixed_rate: float
    pay_times: list[float]
    t0: float = 0.0


@strawberry.input
class FXForwardInput:
    """FX forward: notional in base currency, strike (quote per base), settle at maturity. Uses CIP (base + quote curves)."""

    pair: str
    base_curve: str
    quote_curve: str
    maturity: float
    notional_base: float
    strike: float


@strawberry.input
class MortgageInput:
    """Level-pay mortgage (fixed rate, no prepayment)."""

    curve: str
    notional: float
    annual_rate: float
    term_years: float
    payments_per_year: int


@strawberry.input
class CDSInput:
    """Single-name CDS (protection buyer by default)."""

    discount_curve: str
    survival_curve: str
    notional: float
    premium_rate: float
    pay_times: list[float]
    recovery: float = 0.4
    t0: float = 0.0
    protection_buyer: bool = True


# --- Output types (response payloads) ---


@strawberry.type
class RiskMeasures:
    """Risk measures: PV01 (parallel curve bump), FX delta (spot bump), CS01 (hazard bump)."""

    pv01: Optional[float] = None
    fx_delta: Optional[float] = None
    cs01: Optional[float] = None


@strawberry.type
class PricingResult:
    """Pricing result: NPV and optional risk measures."""

    npv: float
    risk_measures: Optional[RiskMeasures] = None


@strawberry.type
class ValidationError:
    """Structured validation error."""

    message: str
    code: Optional[str] = None
