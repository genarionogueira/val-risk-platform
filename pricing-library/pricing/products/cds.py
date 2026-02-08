"""Single-name CDS product (instrument data only; pricing via PricingEngine)."""

from dataclasses import dataclass


@dataclass
class CDS:
    """
    Single-name credit default swap (protection buyer convention by default).
    Premium leg: fixed spread paid on surviving notional; Protection leg: LGD paid on default.
    Uses discount_curve for DF, survival_curve for S(t) (survival probability).
    PV = pv_protection - pv_premium for protection_buyer=True (computed by PricingEngine).
    """

    discount_curve: str
    survival_curve: str
    notional: float
    premium_rate: float
    pay_times: list[float]
    recovery: float = 0.4
    t0: float = 0.0
    protection_buyer: bool = True
