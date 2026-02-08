"""Client-side types for the Pricing GraphQL API (mirror API contracts)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CurveInput:
    """Curve definition: name, pillars (year fractions), zero rates (continuously compounded)."""

    name: str
    pillars: list[float]
    zero_rates_cc: list[float]
    t0: float = 0.0


@dataclass
class FxSpotInput:
    """FX spot rate for a pair (e.g. EURUSD)."""

    pair: str
    spot: float


@dataclass
class HazardCurveInput:
    """Hazard/survival curve: df(t) returns S(t)."""

    name: str
    pillars: list[float]
    hazard_rates: list[float]
    t0: float = 0.0


@dataclass
class MarketInput:
    """Market snapshot: curves, hazard curves, and FX spots."""

    curves: list[CurveInput]
    hazard_curves: Optional[list[HazardCurveInput]] = None
    fx_spot: Optional[list[FxSpotInput]] = None


@dataclass
class ZeroCouponBondInput:
    """Zero-coupon bond: single cashflow at maturity."""

    curve: str
    maturity: float
    notional: float


@dataclass
class FXForwardInput:
    """FX forward: notional in base currency, strike (quote per base). Uses CIP (base + quote curves)."""

    pair: str
    base_curve: str
    quote_curve: str
    maturity: float
    notional_base: float
    strike: float


@dataclass
class FixedFloatSwapInput:
    """Fixed-float interest rate swap (receive float, pay fixed)."""

    curve: str
    notional: float
    fixed_rate: float
    pay_times: list[float]
    t0: float = 0.0


@dataclass
class MortgageInput:
    """Level-pay mortgage (fixed rate, no prepayment)."""

    curve: str
    notional: float
    annual_rate: float
    term_years: float
    payments_per_year: int


@dataclass
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


@dataclass
class PricingResult:
    """Pricing result: NPV and optional risk measures (flattened for ergonomics)."""

    npv: float
    pv01: Optional[float] = None
    fx_delta: Optional[float] = None
    cs01: Optional[float] = None


@dataclass
class CurveSnapshot:
    """Curve snapshot from marketdata subscription (nested curve in CurveUpdate)."""

    name: str
    pillars: list[float]
    zero_rates_cc: list[float]
    t0: float = 0.0


@dataclass
class CurveUpdate:
    """A curve snapshot plus rate deltas from the previous update. Null for tenors without change."""

    curve: CurveSnapshot
    rate_deltas_cc: list[float | None]
    rate_deltas_bp: list[float | None]


def curve_snapshot_to_curve_input(snapshot: CurveSnapshot) -> CurveInput:
    """Build CurveInput from a CurveSnapshot for use with PricingClient."""
    return CurveInput(
        name=snapshot.name,
        pillars=snapshot.pillars,
        zero_rates_cc=snapshot.zero_rates_cc,
        t0=snapshot.t0,
    )
