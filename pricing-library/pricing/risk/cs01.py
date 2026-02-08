"""CS01 risk measure (bump hazard curve, reprice)."""

from __future__ import annotations

from dataclasses import dataclass

from pricing.interfaces import Instrument
from pricing.market import Market
from pricing.pricing import price
from pricing.risk.base import BaseRiskMeasure


@dataclass
class CS01Parallel(BaseRiskMeasure):
    """CS01: sensitivity to parallel hazard curve shift."""

    hazard_curve_name: str
    bump_bp: float = 1.0

    @property
    def name(self) -> str:
        return f"CS01_{self.hazard_curve_name}"

    def compute(self, instrument: Instrument, market: Market) -> float:
        """PV(bumped) - PV(base) for parallel hazard curve shift."""
        bump = self.bump_bp / 10000.0
        curve = market.curve(self.hazard_curve_name)
        bumped_curve = curve.bumped(bump)
        bumped_market = market.with_curve(self.hazard_curve_name, bumped_curve)
        return price(instrument, bumped_market) - price(instrument, market)
