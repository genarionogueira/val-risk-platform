"""FX delta risk measure (spot bump, finite difference)."""

from __future__ import annotations

from dataclasses import dataclass

from pricing.interfaces import Instrument
from pricing.market import Market
from pricing.pricing import price
from pricing.risk.base import BaseRiskMeasure


@dataclass
class FXDelta(BaseRiskMeasure):
    """FX delta: (PV(bumped) - PV(base)) / (spot_bumped - spot)."""

    pair: str
    bump_pct: float = 0.01

    @property
    def name(self) -> str:
        return f"FXDelta_{self.pair}"

    def compute(self, instrument: Instrument, market: Market) -> float:
        """Finite-difference delta with relative spot bump."""
        spot = market.fx(self.pair)
        spot_bumped = spot * (1.0 + self.bump_pct)
        bumped_market = market.with_fx(self.pair, spot_bumped)
        pv_base = price(instrument, market)
        pv_bumped = price(instrument, bumped_market)
        return (pv_bumped - pv_base) / (spot_bumped - spot)
