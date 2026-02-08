"""
Market snapshot container.

`Market` is intentionally a *simple* in-memory snapshot of the inputs needed for
pricing/risk:
- Discount curves, keyed by a name (e.g. "USD_DISC")
- FX spot rates, keyed by a pair string (e.g. "EURUSD")

We keep this class small so that:
- instruments/products remain data-only
- pricing/risk functions can be pure (market in -> number out)
"""

from __future__ import annotations

from copy import deepcopy

from pricing.interfaces import Curve


class Market:
    """
    Market snapshot: discount curves (by name) and FX spot rates (pair -> rate).
    Immutable-style: with_curve / with_fx return new Market instances.
    """

    def __init__(
        self,
        curves: dict[str, Curve] | None = None,
        fx_spot: dict[str, float] | None = None,
    ) -> None:
        # Defensive copies: callers can keep their own dicts without risking
        # accidental mutation of the Market snapshot (and vice-versa).
        self.curves: dict[str, Curve] = curves.copy() if curves else {}
        self.fx_spot: dict[str, float] = fx_spot.copy() if fx_spot else {}

    def curve(self, name: str) -> Curve:
        """Return curve by name. Raises KeyError if not found."""
        return self.curves[name]

    def fx(self, pair: str) -> float:
        """Return FX spot for pair (e.g. 'EURUSD'). Raises KeyError if not found."""
        return self.fx_spot[pair]

    def with_curve(self, name: str, curve: Curve) -> "Market":
        """Return a new Market with the given curve updated/added."""
        # Use deepcopy to preserve the "immutable snapshot" feel, even if future
        # curve objects become nested/mutable.
        new_curves = deepcopy(self.curves)
        new_curves[name] = curve
        return Market(curves=new_curves, fx_spot=self.fx_spot)

    def with_fx(self, pair: str, spot: float) -> "Market":
        """Return a new Market with the given FX pair updated/added."""
        # Copy-on-write update: keep original snapshot unchanged.
        new_fx = deepcopy(self.fx_spot)
        new_fx[pair] = spot
        return Market(curves=self.curves, fx_spot=new_fx)
