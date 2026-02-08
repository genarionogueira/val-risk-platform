"""Parallel PV01 risk measure (bump-and-reprice)."""

from __future__ import annotations

from dataclasses import dataclass

from pricing.interfaces import Instrument
from pricing.market import Market
from pricing.pricing import price
from pricing.risk.base import BaseRiskMeasure


@dataclass
class PV01Parallel(BaseRiskMeasure):
    """Parallel PV01: sensitivity to parallel curve shift."""

    curve_name: str
    bump_bp: float = 1.0

    @property
    def name(self) -> str:
        return f"PV01_{self.curve_name}"

    def compute(self, instrument: Instrument, market: Market) -> float:
        """PV(bumped) - PV(base) for parallel curve shift."""
        bump = self.bump_bp / 10000.0
        curve = market.curve(self.curve_name)
        bumped_curve = curve.bumped(bump)
        bumped_market = market.with_curve(self.curve_name, bumped_curve)
        return price(instrument, bumped_market) - price(instrument, market)
