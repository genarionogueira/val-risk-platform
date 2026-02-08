"""Marketdata GraphQL subscription client (WebSocket, graphql-transport-ws)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pricing_client.types import CurveSnapshot, CurveUpdate

SUB_QUERY = """
subscription CurveUpdated($name: String!) {
  curveUpdated(name: $name) {
    curve { name pillars t0 zeroRatesCc }
    rateDeltasCc
    rateDeltasBp
  }
}
"""


def _parse_curve(raw: dict) -> CurveSnapshot:
    return CurveSnapshot(
        name=raw["name"],
        pillars=raw["pillars"],
        zero_rates_cc=raw["zeroRatesCc"],
        t0=raw.get("t0", 0.0),
    )


def _parse_update(raw: dict) -> CurveUpdate:
    curve_raw = raw.get("curve") or {}
    return CurveUpdate(
        curve=_parse_curve(curve_raw),
        rate_deltas_cc=raw.get("rateDeltasCc") or [],
        rate_deltas_bp=raw.get("rateDeltasBp") or [],
    )


class MarketdataClient:
    """
    Client for the Marketdata GraphQL subscription (curve updates over WebSocket).
    Use from notebooks or scripts; configurable WebSocket URL for Docker vs local.
    """

    def __init__(self, url: str = "ws://marketdata:8001/graphql", close_timeout: float = 2.0) -> None:
        self._url = url.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")
        self._close_timeout = close_timeout

    async def subscribe_curve_updates(self, name: str) -> AsyncIterator[CurveUpdate]:
        """
        Subscribe to curve updates by name. Yields CurveUpdate for each event.
        WebSocket is closed when the iterator is exhausted or cancelled.
        """
        import websockets

        async with websockets.connect(
            self._url,
            subprotocols=["graphql-transport-ws"],
            close_timeout=self._close_timeout,
        ) as ws:
            await ws.send(json.dumps({"type": "connection_init", "payload": {}}))
            msg = json.loads(await ws.recv())
            if msg.get("type") != "connection_ack":
                raise RuntimeError(f"Unexpected marketdata response: {msg}")

            sub_id = "1"
            await ws.send(
                json.dumps(
                    {
                        "id": sub_id,
                        "type": "subscribe",
                        "payload": {"query": SUB_QUERY, "variables": {"name": name}},
                    }
                )
            )
            try:
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    if msg.get("type") == "next":
                        data = msg.get("payload", {}).get("data", {})
                        cu = data.get("curveUpdated")
                        if cu is not None:
                            yield _parse_update(cu)
                    elif msg.get("type") in ("complete", "error"):
                        break
            finally:
                try:
                    await ws.send(json.dumps({"id": sub_id, "type": "complete"}))
                except Exception:
                    pass
