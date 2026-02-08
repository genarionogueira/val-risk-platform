"""GraphQL types for curve data."""

from typing import Optional

import strawberry


@strawberry.type
class Curve:
    """Zero rate curve: name, pillars (year fractions), zero rates (continuously compounded)."""

    name: str
    pillars: list[float]
    zero_rates_cc: list[float]
    t0: float = 0.0


@strawberry.type
class CurveUpdate:
    """A curve snapshot plus the rate deltas from the previous update. Null for tenors without change."""

    curve: Curve
    rate_deltas_cc: list[Optional[float]]  # change per pillar (decimal); null for unchanged tenors
    rate_deltas_bp: list[Optional[float]]  # same deltas in bp; null for unchanged tenors
