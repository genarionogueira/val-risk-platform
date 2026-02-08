"""Pricer for FX forwards (CIP-based valuation)."""

from __future__ import annotations

from pricing.interfaces import Instrument
from pricing.market import Market
from pricing.pricers.base import BasePricer
from pricing.products.fx import FXForward


class FXPricer(BasePricer):
    """Pricer for FX forwards (covered interest rate parity)."""

    def can_price(self, instrument: Instrument) -> bool:
        return isinstance(instrument, FXForward)

    def npv(self, instrument: Instrument, market: Market) -> float:
        """
        FX forward: F = spot * DF_base(T) / DF_quote(T), PV = notional_base * DF_quote(T) * (F - strike).
        """
        assert isinstance(instrument, FXForward)
        fwd = instrument
        spot = market.fx(fwd.pair)
        df_base = market.curve(fwd.base_curve).df(fwd.maturity)
        df_quote = market.curve(fwd.quote_curve).df(fwd.maturity)
        fwd_rate = spot * df_base / df_quote
        return (
            fwd.notional_base
            * df_quote
            * (fwd_rate - fwd.strike)
        )
