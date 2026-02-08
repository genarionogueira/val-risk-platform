"""GraphQL schema: curve query and subscription."""

import asyncio
from typing import Optional

import strawberry

from app.redis_client import get_redis
from app.store import curve_from_payload, get_curve
from app.types import Curve, CurveUpdate

STREAM_PREFIX = "curve_updates"
XREAD_BLOCK_MS = 5000


@strawberry.type
class Query:
    @strawberry.field
    def curve(self, name: str) -> Optional[Curve]:
        """Return curve by name, or null if not found."""
        return get_curve(name)


_EPS = 1e-12


def _rate_deltas(prev_rates: list[float], new_rates: list[float]) -> list[float]:
    """Per-pillar rate change (decimal). Pads with 0 if lengths differ."""
    n = max(len(prev_rates), len(new_rates))
    prev = (prev_rates + [0.0] * n)[:n]
    new = (new_rates + [0.0] * n)[:n]
    return [new[i] - prev[i] for i in range(n)]


def _deltas_null_unchanged(deltas_cc: list[float]) -> tuple[list[float | None], list[float | None]]:
    """Return (rate_deltas_cc, rate_deltas_bp) with None for unchanged tenors."""
    out_cc: list[float | None] = []
    out_bp: list[float | None] = []
    for d in deltas_cc:
        if abs(d) < _EPS:
            out_cc.append(None)
            out_bp.append(None)
        else:
            out_cc.append(d)
            out_bp.append(d * 10000.0)
    return out_cc, out_bp


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def curve_updated(self, name: str) -> Optional[CurveUpdate]:
        """Subscribe to curve updates by name. Yields current curve + deltas; then streams from Redis with deltas."""
        curve = get_curve(name)
        prev_rates: list[float] = []
        if curve is not None:
            # First event: full curve, deltas all null (no previous data)
            n = len(curve.zero_rates_cc)
            prev_rates = list(curve.zero_rates_cc)
            yield CurveUpdate(
                curve=curve,
                rate_deltas_cc=[None] * n,
                rate_deltas_bp=[None] * n,
            )
        redis = await get_redis()
        stream_key = f"{STREAM_PREFIX}:{name}"
        last_id = "$"
        while True:
            try:
                result = await redis.xread(
                    {stream_key: last_id},
                    block=XREAD_BLOCK_MS,
                    count=1,
                )
                if not result:
                    continue
                for stream, messages in result:
                    for msg_id, fields in messages:
                        last_id = msg_id
                        payload = fields.get("payload")
                        if payload is None:
                            continue
                        parsed = curve_from_payload(payload)
                        if parsed is not None:
                            deltas = _rate_deltas(prev_rates, list(parsed.zero_rates_cc))
                            prev_rates = list(parsed.zero_rates_cc)
                            deltas_cc, deltas_bp = _deltas_null_unchanged(deltas)
                            yield CurveUpdate(curve=parsed, rate_deltas_cc=deltas_cc, rate_deltas_bp=deltas_bp)
            except (Exception, asyncio.CancelledError):
                break


schema = strawberry.Schema(query=Query, subscription=Subscription)
