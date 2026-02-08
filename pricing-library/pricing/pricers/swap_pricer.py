"""Pricer for fixed-float interest rate swaps (single curve)."""

from __future__ import annotations

from pricing.interfaces import Curve, Instrument
from pricing.market import Market
from pricing.pricers.base import BasePricer
from pricing.products.swap import FixedFloatSwap


class SwapPricer(BasePricer):
    """Pricer for fixed-float interest rate swaps (single curve)."""

    def can_price(self, instrument: Instrument) -> bool:
        return isinstance(instrument, FixedFloatSwap)

    def npv(self, instrument: Instrument, market: Market) -> float:
        """
        Fixed-float swap (single curve).
        Convention: receive float, pay fixed. PV = PV(float leg) - PV(fixed leg).
        """
        assert isinstance(instrument, FixedFloatSwap)
        swap = instrument
        c = market.curve(swap.curve)
        pv_fixed = self._pv_fixed_leg(swap, c)
        pv_float = self._pv_float_leg(swap, c)
        return pv_float - pv_fixed

    @staticmethod
    def _pv_fixed_leg(swap: FixedFloatSwap, c: Curve) -> float:
        """
        Fixed leg PV.
        We infer accrual fractions from successive pay times.
        CF_i = notional * fixed_rate * accrual_i, PV = sum_i CF_i * DF(t_i).
        """
        pv = 0.0
        prev = swap.t0
        for t in swap.pay_times:
            accrual = t - prev
            pv += swap.notional * swap.fixed_rate * accrual * c.df(t)
            prev = t
        return pv

    @staticmethod
    def _pv_float_leg(swap: FixedFloatSwap, c: Curve) -> float:
        """
        Float leg PV (single-curve).
        Forward rate from discount factors: f = (DF(prev)/DF(t) - 1) / accrual.
        """
        pv = 0.0
        prev = swap.t0
        df_prev = c.df(prev)
        for t in swap.pay_times:
            accrual = t - prev
            df_t = c.df(t)
            fwd = (df_prev / df_t - 1.0) / accrual if accrual > 0 else 0.0
            cf = swap.notional * fwd * accrual
            pv += cf * df_t
            prev = t
            df_prev = df_t
        return pv
