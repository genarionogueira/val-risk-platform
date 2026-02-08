"""Base pricer abstract class for instrument pricing implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pricing.interfaces import Instrument
from pricing.market import Market


class BasePricer(ABC):
    """Abstract base class for instrument pricers.

    Subclasses implement can_price() and npv() for specific instrument types.
    This allows pricing logic to be isolated, testable, and pluggable.
    """

    @abstractmethod
    def can_price(self, instrument: Instrument) -> bool:
        """Return True if this pricer handles the instrument type."""
        ...

    @abstractmethod
    def npv(self, instrument: Instrument, market: Market) -> float:
        """Compute present value."""
        ...
