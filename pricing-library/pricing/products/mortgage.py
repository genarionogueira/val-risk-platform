"""Level-pay mortgage product (instrument data only; pricing via PricingEngine)."""

from dataclasses import dataclass


@dataclass
class LevelPayMortgage:
    """
    Fixed-rate level-payment mortgage (no prepayment).
    Value to lender = PV of all level payments discounted with the curve.
    """

    curve: str
    notional: float
    annual_rate: float
    term_years: float
    payments_per_year: int
