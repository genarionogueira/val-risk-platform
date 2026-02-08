"""Pricer for zero-coupon bonds."""

from __future__ import annotations

from pricing.interfaces import Instrument
from pricing.market import Market
from pricing.pricers.base import BasePricer
from pricing.products.bond import ZeroCouponBond


class BondPricer(BasePricer):
    """Pricer for zero-coupon bonds."""

    def can_price(self, instrument: Instrument) -> bool:
        return isinstance(instrument, ZeroCouponBond)

    def npv(self, instrument: Instrument, market: Market) -> float:
        """Zero-coupon bond: PV = notional * DF(maturity)."""
        assert isinstance(instrument, ZeroCouponBond)
        bond = instrument
        c = market.curve(bond.curve)
        return bond.notional * c.df(bond.maturity)
