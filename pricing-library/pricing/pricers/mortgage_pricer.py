"""Pricer for level-pay fixed-rate mortgages."""

from __future__ import annotations

from pricing.interfaces import Instrument
from pricing.market import Market
from pricing.pricers.base import BasePricer
from pricing.products.mortgage import LevelPayMortgage


class MortgagePricer(BasePricer):
    """Pricer for level-pay fixed-rate mortgages (no prepayment, no default)."""

    def can_price(self, instrument: Instrument) -> bool:
        return isinstance(instrument, LevelPayMortgage)

    def npv(self, instrument: Instrument, market: Market) -> float:
        """
        Level-pay mortgage: constant payment from annuity formula,
        PV = sum of payment * DF(t_i) over pay_times.
        """
        assert isinstance(instrument, LevelPayMortgage)
        m = instrument
        c = market.curve(m.curve)
        n = int(m.term_years * m.payments_per_year)
        r = m.annual_rate / m.payments_per_year
        if r == 0:
            payment = m.notional / n
        else:
            payment = (
                m.notional
                * (r * (1 + r) ** n)
                / ((1 + r) ** n - 1)
            )
        pay_times = [
            i / m.payments_per_year for i in range(1, n + 1)
        ]
        return sum(payment * c.df(t) for t in pay_times)
