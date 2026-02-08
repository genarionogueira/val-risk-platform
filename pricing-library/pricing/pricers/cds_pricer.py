"""Pricer for single-name CDS."""

from __future__ import annotations

from pricing.interfaces import Curve, Instrument
from pricing.market import Market
from pricing.pricers.base import BasePricer
from pricing.products.cds import CDS


class CDSPricer(BasePricer):
    """Pricer for single-name CDS (premium + protection legs, discrete default)."""

    def can_price(self, instrument: Instrument) -> bool:
        return isinstance(instrument, CDS)

    def npv(self, instrument: Instrument, market: Market) -> float:
        """
        CDS NPV for protection buyer: pv_protection - pv_premium.
        Flip sign if protection_buyer=False.
        """
        assert isinstance(instrument, CDS)
        cds = instrument
        disc = market.curve(cds.discount_curve)
        surv = market.curve(cds.survival_curve)
        pv_premium = self._pv_premium_leg(cds, disc, surv)
        pv_protection = self._pv_protection_leg(cds, disc, surv)
        npv = pv_protection - pv_premium
        return npv if cds.protection_buyer else -npv

    @staticmethod
    def _pv_premium_leg(cds: CDS, disc: Curve, surv: Curve) -> float:
        """Premium leg: sum_i N * s * accrual_i * DF(t_i) * S(t_i)."""
        pv = 0.0
        prev = cds.t0
        for t in cds.pay_times:
            accrual = t - prev
            pv += (
                cds.notional
                * cds.premium_rate
                * accrual
                * disc.df(t)
                * surv.df(t)
            )
            prev = t
        return pv

    @staticmethod
    def _pv_protection_leg(cds: CDS, disc: Curve, surv: Curve) -> float:
        """Protection leg (discrete): sum_i N(1-R) * DF(t_mid) * (S(t_{i-1}) - S(t_i))."""
        pv = 0.0
        prev = cds.t0
        s_prev = surv.df(prev)
        for t in cds.pay_times:
            s_t = surv.df(t)
            t_mid = (prev + t) / 2.0
            prob_default = s_prev - s_t
            pv += (
                cds.notional
                * (1.0 - cds.recovery)
                * disc.df(t_mid)
                * prob_default
            )
            prev = t
            s_prev = s_t
        return pv

    @staticmethod
    def fair_spread(cds: CDS, market: Market) -> float:
        """Fair spread s* such that NPV=0: s* = pv_protection / risky_annuity."""
        disc = market.curve(cds.discount_curve)
        surv = market.curve(cds.survival_curve)
        pv_protection = CDSPricer._pv_protection_leg(cds, disc, surv)
        risky_annuity = 0.0
        prev = cds.t0
        for t in cds.pay_times:
            accrual = t - prev
            risky_annuity += cds.notional * accrual * disc.df(t) * surv.df(t)
            prev = t
        if risky_annuity <= 0:
            return 0.0
        return pv_protection / risky_annuity
