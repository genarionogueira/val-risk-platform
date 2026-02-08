"""Python client for the Pricing GraphQL API."""

from pricing_client.client import PricingClient
from pricing_client.marketdata import MarketdataClient
from pricing_client.types import (
    CDSInput,
    CurveInput,
    CurveSnapshot,
    CurveUpdate,
    FXForwardInput,
    FixedFloatSwapInput,
    FxSpotInput,
    HazardCurveInput,
    MarketInput,
    MortgageInput,
    PricingResult,
    ZeroCouponBondInput,
    curve_snapshot_to_curve_input,
)

try:
    from pricing_client.blotter import LiveBlotter, stream_live_blotter
except ImportError:
    LiveBlotter = None  # type: ignore[misc, assignment]
    stream_live_blotter = None  # type: ignore[misc, assignment]

__all__ = [
    "CDSInput",
    "CurveInput",
    "CurveSnapshot",
    "CurveUpdate",
    "FXForwardInput",
    "FixedFloatSwapInput",
    "FxSpotInput",
    "HazardCurveInput",
    "LiveBlotter",
    "MarketInput",
    "MarketdataClient",
    "MortgageInput",
    "PricingClient",
    "PricingResult",
    "ZeroCouponBondInput",
    "curve_snapshot_to_curve_input",
    "stream_live_blotter",
]
