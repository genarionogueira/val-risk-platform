"""
Pricing engine: computes NPV for instruments given a market snapshot.

Design intent:
- Instruments/products are **data only** (no market access, no pricing methods).
- This engine uses a **registry of pricers** for dispatch, enabling:
  - Adding new instruments without modifying engine code (Open/Closed Principle)
  - Swapping pricing models per instrument type
  - Third-party pricer plugins
"""

from __future__ import annotations

from pricing.interfaces import Instrument
from pricing.market import Market
from pricing.pricers import BasePricer


class PricingEngine:
    """
    Registry-based pricing engine.

    Pricers are registered at initialization and dispatched based on
    can_price() checks. First matching pricer wins.
    """

    def __init__(self) -> None:
        self._pricers: list[BasePricer] = []

    def register(self, pricer: BasePricer) -> None:
        """Register a pricer for dispatch.

        Order matters: first matching pricer wins.
        """
        self._pricers.append(pricer)

    def npv(self, instrument: Instrument, market: Market) -> float:
        """Dispatch to appropriate pricer."""
        for pricer in self._pricers:
            if pricer.can_price(instrument):
                return pricer.npv(instrument, market)
        raise ValueError(
            f"No pricer registered for {type(instrument).__name__}. "
            "Register a pricer with engine.register(pricer)."
        )


def create_default_engine() -> PricingEngine:
    """Factory for default engine with all built-in pricers registered."""
    from pricing.pricers import (
        BondPricer,
        CDSPricer,
        FXPricer,
        MortgagePricer,
        SwapPricer,
    )

    engine = PricingEngine()
    engine.register(BondPricer())
    engine.register(SwapPricer())
    engine.register(FXPricer())
    engine.register(MortgagePricer())
    engine.register(CDSPricer())
    return engine
