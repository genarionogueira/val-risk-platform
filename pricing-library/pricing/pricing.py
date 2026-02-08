"""
Pricing entrypoint.

Most users of the library should only need `price(trade, market)`.
It delegates to a default `PricingEngine` instance that contains the pricing logic.

Keeping this as a thin wrapper gives you a stable, ergonomic API while still
allowing advanced users to instantiate/configure their own engines.
"""

from typing import TypeAlias

from pricing.engine import create_default_engine
from pricing.market import Market
from pricing.products.bond import ZeroCouponBond
from pricing.products.cds import CDS
from pricing.products.fx import FXForward
from pricing.products.mortgage import LevelPayMortgage
from pricing.products.swap import FixedFloatSwap


Trade: TypeAlias = (
    ZeroCouponBond | CDS | FixedFloatSwap | FXForward | LevelPayMortgage
)

_default_engine = create_default_engine()


def price(trade: Trade, market: Market) -> float:
    """Return present value of trade (via default registry-based engine)."""
    # One place to hook cross-cutting concerns later (tracing, caching, validation).
    return _default_engine.npv(trade, market)
