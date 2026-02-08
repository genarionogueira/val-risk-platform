"""Simulated real-time feed: periodically publish curve updates to Redis stream."""

import asyncio
import random

from app.redis_client import get_redis
from app.store import curve_to_payload, get_curve, set_curve
from app.types import Curve

STREAM_PREFIX = "curve_updates"
FEED_INTERVAL_SEC = 0.5  # Demo: faster ticks for real-time feel
# Random delta (bp) range per rate to simulate real-time market moves
RATE_DELTA_BP_MIN = -1.0
RATE_DELTA_BP_MAX = 1.0


async def run_feed() -> None:
    """Background task: every FEED_INTERVAL_SEC, bump sample curve and XADD to Redis."""
    redis = await get_redis()
    # Seed stream so subscription XREAD does not wait on empty stream
    curve = get_curve("USD_DISC")
    if curve is not None:
        stream_key = f"{STREAM_PREFIX}:{curve.name}"
        await redis.xadd(stream_key, {"payload": curve_to_payload(curve)}, maxlen=1000)
    while True:
        try:
            curve = get_curve("USD_DISC")
            if curve is None:
                await asyncio.sleep(FEED_INTERVAL_SEC)
                continue
            # Apply random delta (bp) to multiple random pillars to simulate real-time market moves
            rates = list(curve.zero_rates_cc)
            n_pillars = len(rates)
            n_to_change = min(random.randint(2, 4), n_pillars)  # 2–4 tenors per tick
            indices = random.sample(range(n_pillars), n_to_change)
            for idx in indices:
                delta_bp = random.uniform(RATE_DELTA_BP_MIN, RATE_DELTA_BP_MAX)
                rates[idx] = rates[idx] + (delta_bp / 10000.0)
            updated = Curve(
                name=curve.name,
                pillars=curve.pillars,
                zero_rates_cc=rates,
                t0=curve.t0,
            )
            set_curve(curve.name, updated)
            stream_key = f"{STREAM_PREFIX}:{curve.name}"
            payload = curve_to_payload(updated)
            await redis.xadd(stream_key, {"payload": payload}, maxlen=1000)
        except asyncio.CancelledError:
            break
        except Exception:
            pass
        await asyncio.sleep(FEED_INTERVAL_SEC)
