"""
Risk measures implemented via "bump and reprice".

New code should use PV01Parallel, FXDelta, and CS01Parallel classes for composability.
Legacy functions pv01_parallel, fx_delta, and cs01_parallel are preserved for backward compatibility.
"""

from __future__ import annotations

from pricing.market import Market
from pricing.pricing import Trade
from pricing.risk.base import BaseRiskMeasure
from pricing.risk.cs01 import CS01Parallel
from pricing.risk.fx_delta import FXDelta
from pricing.risk.pv01 import PV01Parallel


def pv01_parallel(
    trade: Trade,
    market: Market,
    curve_name: str,
    bump_bp: float = 1.0,
) -> float:
    """
    PV01: change in PV when the curve is bumped by bump_bp basis points (parallel).
    bump_bp is in basis points; bump = bump_bp / 10000 (additive to zero rates).
    Returns PV(bumped) - PV(base).
    """
    measure = PV01Parallel(curve_name=curve_name, bump_bp=bump_bp)
    return measure.compute(trade, market)


def fx_delta(
    trade: Trade,
    market: Market,
    pair: str,
    bump_pct: float = 0.01,
) -> float:
    """
    FX delta: (PV(bumped) - PV(base)) / (spot_bumped - spot).
    Spot is bumped by factor (1 + bump_pct).
    """
    measure = FXDelta(pair=pair, bump_pct=bump_pct)
    return measure.compute(trade, market)


def cs01_parallel(
    trade: Trade,
    market: Market,
    hazard_curve_name: str,
    bump_bp: float = 1.0,
) -> float:
    """
    CS01: change in PV when the hazard curve is bumped by bump_bp basis points (parallel).
    Returns PV(bumped) - PV(base).
    """
    measure = CS01Parallel(hazard_curve_name=hazard_curve_name, bump_bp=bump_bp)
    return measure.compute(trade, market)


__all__ = [
    "BaseRiskMeasure",
    "PV01Parallel",
    "FXDelta",
    "CS01Parallel",
    "pv01_parallel",
    "fx_delta",
    "cs01_parallel",
]
