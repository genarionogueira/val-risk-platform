"""Fixed-float interest rate swap (single-curve; instrument data only; pricing via PricingEngine)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FixedFloatSwap:
    """
    Fixed vs float swap (single curve).
    Receive float, pay fixed.
    PV = PV_float_leg - PV_fixed_leg (computed by PricingEngine).
    pay_times: payment times (year-fractions); accruals inferred as differences from t0.
    """

    curve: str
    notional: float
    fixed_rate: float
    pay_times: list[float]
    t0: float = 0.0
