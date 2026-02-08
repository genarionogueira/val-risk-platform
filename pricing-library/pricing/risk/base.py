"""Base class for risk measure implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pricing.interfaces import Instrument
from pricing.market import Market


class BaseRiskMeasure(ABC):
    """Base class for risk measure implementations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        ...

    @abstractmethod
    def compute(self, instrument: Instrument, market: Market) -> float:
        """Compute the risk measure value."""
        ...
