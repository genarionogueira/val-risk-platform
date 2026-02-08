# Pricing Library

Core valuation and risk library: curves, market snapshots, product models, pricing engine, and risk measures (PV01, FX delta, CS01). Designed for extensibility via Protocol-based interfaces and a registry-based pricing engine.

## Contents

- **Interfaces** — `Curve`, `Instrument`, `Pricer`, `RiskMeasure` (Protocols for extension points)
- **Curves** — `ZeroRateCurve` (linear interpolation, discount factors, parallel bump); `HazardRateCurve` (survival S(t), df(t)=S(t))
- **Market** — `Market` (curves + FX spots; immutable-style updates; accepts any `Curve` implementation)
- **Products** — `ZeroCouponBond`, `FixedFloatSwap`, `FXForward`, `LevelPayMortgage`, `CDS`
- **Pricing** — `PricingEngine` (registry of pricers), `create_default_engine()`, `price(trade, market)`
- **Pricers** — `BasePricer`, `BondPricer`, `SwapPricer`, `FXPricer`, `MortgagePricer`, `CDSPricer`
- **Risk** — `pv01_parallel`, `fx_delta`, `cs01_parallel` (legacy functions); `PV01Parallel`, `FXDelta`, `CS01Parallel` (composable classes)

## Credit (CDS)

Single-name CDS uses a **discount curve** (DF) and a **survival curve** (S(t)). The library reuses the `Curve` protocol: `HazardRateCurve` implements `Curve` where `df(t)` returns survival probability S(t), not a discount factor. CS01 is the sensitivity to a parallel bump of the hazard curve (bump-and-reprice).

## Setup

```bash
poetry install
```

## Run demo

```bash
poetry run python -m pricing.demo
```

## Run tests

```bash
poetry run pytest -q
```

## Package layout

- `pricing/interfaces.py` — Protocol definitions (Curve, Instrument, Pricer, RiskMeasure)
- `pricing/curves.py` — Zero rate curve and HazardRateCurve (both implement Curve protocol)
- `pricing/market.py` — Market snapshot
- `pricing/products/` — Product data models
- `pricing/pricers/` — Pricer implementations (BasePricer, BondPricer, SwapPricer, FXPricer, MortgagePricer, CDSPricer)
- `pricing/engine.py` — Registry-based pricing engine, `create_default_engine()`
- `pricing/pricing.py` — Price dispatch
- `pricing/risk/` — Risk measure classes (PV01Parallel, FXDelta, CS01Parallel) and legacy function wrappers
- `pricing/demo.py` — Sample demo

Time is in year-fractions; rates are continuously compounded. No calendars or day-count conventions.

## Extensibility

The library uses Protocol-based interfaces for all extension points. You can add new curve types, instruments, and risk measures without modifying core code.

### Adding a new curve type

Implement the `Curve` protocol (attributes `name`, methods `df(t)` and `bumped(bump)`):

```python
from pricing.interfaces import Curve
from pricing.market import Market

class SplineCurve:
    name: str = "SPLINE"

    def df(self, t: float) -> float:
        # Your spline interpolation logic
        ...

    def bumped(self, bump: float) -> "SplineCurve":
        # Return new bumped curve
        ...

market = Market(curves={"SPLINE": SplineCurve()})
```

### Adding a new instrument

Define your product and register a pricer with the engine:

```python
from dataclasses import dataclass
from pricing.pricers.base import BasePricer
from pricing.engine import create_default_engine
from pricing.market import Market

@dataclass
class CapFloor:
    curve: str
    strike: float
    # ... your fields ...

class CapFloorPricer(BasePricer):
    def can_price(self, instrument):
        return isinstance(instrument, CapFloor)

    def npv(self, instrument, market):
        # Your pricing logic
        ...

engine = create_default_engine()
engine.register(CapFloorPricer())
# Now engine.npv(CapFloor(...), market) works
```

### Adding a new risk measure

Implement the `RiskMeasure` protocol (property `name`, method `compute(instrument, market)`):

```python
from dataclasses import dataclass
from pricing.risk.base import BaseRiskMeasure

@dataclass
class Gamma(BaseRiskMeasure):
    curve_name: str
    bump_bp: float = 1.0

    @property
    def name(self) -> str:
        return f"Gamma_{self.curve_name}"

    def compute(self, instrument, market):
        # Second-order finite difference
        ...
```
