"""Zero-coupon bond product (instrument data only; pricing via PricingEngine)."""

from dataclasses import dataclass


@dataclass
class ZeroCouponBond:
    """
    Zero-coupon bond: single cashflow at maturity.
    PV = notional * DF(maturity) on the given curve (computed by PricingEngine).
    """

    curve: str
    maturity: float
    notional: float
