"""
Protocol-based interfaces for all extension points in the pricing library.

Using typing.Protocol enables structural subtyping: any class that implements
the required methods satisfies the protocol without explicit inheritance.
This keeps the library open for extension (new curves, pricers, risk measures)
without modifying core code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pricing.market import Market


@runtime_checkable
class Curve(Protocol):
    """Protocol for discount curve implementations.

    Any class implementing df() and bumped() can be used as a curve,
    enabling SplineCurve, NelsonSiegelCurve, etc. without changes to Market.
    """

    name: str

    def df(self, t: float) -> float:
        """Return discount factor to time t (year-fraction)."""
        ...

    def bumped(self, bump: float) -> Curve:
        """Return new curve with parallel additive rate shift."""
        ...


@runtime_checkable
class Instrument(Protocol):
    """Marker protocol for all priceable instruments.

    Instruments are data-only; pricing logic lives in Pricer implementations.
    """

    pass


class Pricer(Protocol):
    """Protocol for instrument pricing implementations.

    Each pricer handles one or more instrument types and can be registered
    with the PricingEngine for dispatch.
    """

    def can_price(self, instrument: Instrument) -> bool:
        """Return True if this pricer handles the given instrument type."""
        ...

    def npv(self, instrument: Instrument, market: Market) -> float:
        """Compute present value in the appropriate currency."""
        ...


class RiskMeasure(Protocol):
    """Protocol for risk measure implementations.

    Risk measures are composable objects that compute sensitivities
    (PV01, delta, gamma, etc.) via bump-and-reprice or analytic formulas.
    """

    @property
    def name(self) -> str:
        """Human-readable name (e.g., 'PV01_USD', 'FXDelta_EURUSD')."""
        ...

    def compute(self, instrument: Instrument, market: Market) -> float:
        """Compute the risk measure value."""
        ...
