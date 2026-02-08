"""In-memory curve store with sample data and Curve serialization for Redis."""

import json
from typing import Any

from app.types import Curve

# Sample USD curve (same pillars/rates as api README and pricing demo)
_SAMPLE_USD = Curve(
    name="USD_DISC",
    pillars=[0.5, 1.0, 2.0, 5.0, 10.0],
    zero_rates_cc=[0.045, 0.043, 0.040, 0.038, 0.037],
    t0=0.0,
)

_curves: dict[str, Curve] = {
    "USD_DISC": _SAMPLE_USD,
}


def get_curve(name: str) -> Curve | None:
    """Return curve by name, or None if not found."""
    return _curves.get(name)


def set_curve(name: str, curve: Curve) -> None:
    """Store or update a curve by name. For future use (e.g. mutations or feed)."""
    _curves[name] = curve


def curve_to_payload(curve: Curve) -> str:
    """Serialize Curve to JSON string for Redis stream payload."""
    return json.dumps({
        "name": curve.name,
        "pillars": curve.pillars,
        "zero_rates_cc": curve.zero_rates_cc,
        "t0": curve.t0,
    })


def curve_from_payload(payload: str) -> Curve | None:
    """Deserialize JSON string from Redis to Curve; return None if invalid."""
    try:
        d: dict[str, Any] = json.loads(payload)
        return Curve(
            name=d["name"],
            pillars=d["pillars"],
            zero_rates_cc=d["zero_rates_cc"],
            t0=d.get("t0", 0.0),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
