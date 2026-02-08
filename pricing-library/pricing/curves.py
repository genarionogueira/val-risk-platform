"""
Interest-rate and credit curve primitives.

This module deliberately keeps curve math minimal and explicit:
- Times are **year fractions** (e.g. 2.0 = 2Y from the curve reference).
- Rates are **continuously compounded zero rates** (ZeroRateCurve).
- Interpolation is **linear in zero rates** between pillar points.
- HazardRateCurve: `df(t)` returns survival probability S(t), not discount factor.

Those choices make the pricing formulas easy to read/verify and keep the library
focused on clean interfaces rather than full-blown market conventions
(day-count, calendars, bootstrapping, etc.).
"""

import math
from dataclasses import dataclass

from pricing.interfaces import Curve


@dataclass
class ZeroRateCurve:
    """
    Zero rate curve (continuously compounded) with linear interpolation.

    - **Pillars** are increasing times (year fractions) where the curve is defined.
    - `zero_rates_cc[i]` is the CC zero rate at `pillars[i]`.
    - `t0` is kept for completeness (reference time) but this curve assumes the
      caller passes times already measured from that reference.

    Implements Curve protocol structurally (no explicit inheritance).
    """

    name: str
    pillars: list[float]
    zero_rates_cc: list[float]
    t0: float = 0.0

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if len(self.pillars) != len(self.zero_rates_cc):
            raise ValueError("pillars and zero_rates_cc must have the same length")
        for i in range(1, len(self.pillars)):
            if self.pillars[i] <= self.pillars[i - 1]:
                raise ValueError("pillars must be strictly increasing")

    def zero_rate_cc(self, t: float) -> float:
        """
        Continuously compounded zero rate at time t (year-fraction).
        Linear interpolation in zero rates. t must be >= 0.
        """
        if t < 0:
            raise ValueError("t must be >= 0")
        if not self.pillars:
            raise ValueError("curve has no pillars")
        # Flat extrapolation beyond the end pillars keeps behavior predictable for
        # demos/tests (avoid accidental blow-ups when requesting small/large times).
        if t <= self.pillars[0]:
            return self.zero_rates_cc[0]
        if t >= self.pillars[-1]:
            return self.zero_rates_cc[-1]
        for i in range(len(self.pillars) - 1):
            if self.pillars[i] <= t <= self.pillars[i + 1]:
                t0, t1 = self.pillars[i], self.pillars[i + 1]
                r0, r1 = self.zero_rates_cc[i], self.zero_rates_cc[i + 1]
                # Linear interpolation in *rates* (not discount factors).
                # This is a common simple choice for toy curves; production systems
                # often interpolate log-DFs or use splines.
                return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
        return self.zero_rates_cc[-1]

    def df(self, t: float) -> float:
        r"""
        Discount factor to time t.

        With CC zero rate r(t), the discount factor is:
        DF(t) = exp(-r(t)*t).
        """
        r = self.zero_rate_cc(t)
        return math.exp(-r * t)

    def bumped(self, bump: float) -> "ZeroRateCurve":
        """
        Return a new curve with a *parallel* additive shift to all zero rates.

        This is the standard "bump-and-reprice" building block for PV01-style
        sensitivities. `bump` is expressed in absolute rate terms (e.g. 1bp = 0.0001).
        """
        new_rates = [r + bump for r in self.zero_rates_cc]
        return ZeroRateCurve(
            name=self.name,
            pillars=list(self.pillars),
            zero_rates_cc=new_rates,
            t0=self.t0,
        )


@dataclass
class HazardRateCurve:
    """
    Hazard rate curve with piecewise-constant hazard between pillars.

    Implements Curve protocol structurally. Here `df(t)` returns **survival probability**
    S(t) = exp(-integral of hazard), not a discount factor. Used as the survival curve
    in CDS pricing.
    - pillars[i], hazard_rates[i]: hazard is hazard_rates[i] in segment [prev, pillars[i]]
      (prev=0 for first segment, then pillars[i-1]).
    - bumped(bump) adds `bump` to all hazard rates (absolute; 1bp = 0.0001).
    """

    name: str
    pillars: list[float]
    hazard_rates: list[float]
    t0: float = 0.0

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if len(self.pillars) != len(self.hazard_rates):
            raise ValueError("pillars and hazard_rates must have the same length")
        for i in range(1, len(self.pillars)):
            if self.pillars[i] <= self.pillars[i - 1]:
                raise ValueError("pillars must be strictly increasing")

    def hazard_rate(self, t: float) -> float:
        """Piecewise-constant hazard at time t. Flat extrapolation beyond endpoints."""
        if t < 0:
            raise ValueError("t must be >= 0")
        if not self.pillars:
            raise ValueError("curve has no pillars")
        if t <= self.pillars[0]:
            return self.hazard_rates[0]
        if t >= self.pillars[-1]:
            return self.hazard_rates[-1]
        for i in range(len(self.pillars) - 1):
            if self.pillars[i] <= t <= self.pillars[i + 1]:
                return self.hazard_rates[i]
        return self.hazard_rates[-1]

    def df(self, t: float) -> float:
        """
        Survival probability S(t) = exp(-integral_0^t h(u) du).
        Implements Curve protocol: for HazardRateCurve, df(t) means S(t).
        """
        if t <= 0:
            return 1.0
        if not self.pillars:
            raise ValueError("curve has no pillars")
        # Piecewise integral: hazard_rates[i] applies in [prev, pillars[i]]
        integral = 0.0
        prev = self.t0
        for i in range(len(self.pillars)):
            t_end = min(self.pillars[i], t)
            if t_end > prev:
                integral += self.hazard_rates[i] * (t_end - prev)
            prev = self.pillars[i]
            if prev >= t:
                break
        if t > self.pillars[-1]:
            integral += self.hazard_rates[-1] * (t - self.pillars[-1])
        return math.exp(-integral)

    def bumped(self, bump: float) -> "HazardRateCurve":
        """Return new curve with parallel additive shift to all hazard rates."""
        new_rates = [h + bump for h in self.hazard_rates]
        return HazardRateCurve(
            name=self.name,
            pillars=list(self.pillars),
            hazard_rates=new_rates,
            t0=self.t0,
        )
