# Pricing Client

Python client for the Pricing GraphQL API, built with [sgqlc](https://github.com/profusion/sgqlc). Intended for use from Jupyter notebooks or scripts so quants can call the API with typed inputs and results, without dealing with HTTP/GraphQL directly.

## Installation

From the repo root (or from `client/`):

```bash
pip install -e ./client
```

In Docker (Jupyter), the client is installed automatically when the notebook service starts.

For the **live blotter** (Jupyter), install the optional jupyter dependencies: `poetry install --with jupyter` (or `pip install ipywidgets pandas` in your environment).

## Usage

```python
from pricing_client import PricingClient, CurveInput, MarketInput, ZeroCouponBondInput

# Default URL is http://api:8000/graphql (for use inside Docker network)
client = PricingClient()

# From host machine (e.g. local API):
# client = PricingClient("http://localhost:8000/graphql")

print(client.hello("Quant Team"))
print(client.version())
```

## Pricing: zero-coupon bond

Build market and bond with the client types, then call `price_zero_coupon_bond`. The method returns a `PricingResult` with `npv` and optional `pv01`.

```python
from pricing_client import CurveInput, MarketInput, ZeroCouponBondInput, PricingClient

client = PricingClient()

# Market: one USD curve
curve = CurveInput(
    name="USD_DISC",
    pillars=[0.5, 1.0, 2.0, 5.0, 10.0],
    zero_rates_cc=[0.045, 0.043, 0.040, 0.038, 0.037],
)
market = MarketInput(curves=[curve])

# Bond: 2Y, 1M notional
bond = ZeroCouponBondInput(curve="USD_DISC", maturity=2.0, notional=1_000_000)

result = client.price_zero_coupon_bond(bond, market, calculate_pv01=True)
print(f"NPV: {result.npv:,.2f}, PV01: {result.pv01:,.2f}")
```

## Pricing: CDS

Build market with discount and hazard curves, then call `price_cds`. The method returns a `PricingResult` with `npv` and optional `cs01`.

```python
from pricing_client import (
    CDSInput,
    CurveInput,
    HazardCurveInput,
    MarketInput,
    PricingClient,
)

client = PricingClient()

# Market: discount curve + hazard (survival) curve
disc_curve = CurveInput(
    name="USD_DISC",
    pillars=[0.5, 1.0, 2.0, 5.0, 10.0],
    zero_rates_cc=[0.045, 0.043, 0.040, 0.038, 0.037],
)
hazard_curve = HazardCurveInput(
    name="CORP_HAZ",
    pillars=[0.5, 1.0, 2.0, 5.0, 10.0],
    hazard_rates=[0.01] * 5,
)
market = MarketInput(curves=[disc_curve], hazard_curves=[hazard_curve])

# CDS: 5Y, 10M notional, 100bp spread, protection buyer
cds = CDSInput(
    discount_curve="USD_DISC",
    survival_curve="CORP_HAZ",
    notional=10_000_000,
    premium_rate=0.01,
    pay_times=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
    recovery=0.4,
)

result = client.price_cds(cds, market, calculate_cs01=True)
print(f"NPV: {result.npv:,.2f}, CS01: {result.cs01:,.2f}")
```

## Real-time curve streaming

Use **stream_curve_and_risk** to display curve and product/risk in two rows (curve on row 1, product+NPV/PV01 on row 2). The display refreshes in place. Runs until interrupted (Ctrl+C) or until `max_updates` if set. See the Jupyter demo notebook (`jupyter/demo.ipynb`).

```python
from pricing_client import PricingClient, ZeroCouponBondInput

client = PricingClient("http://api:8000/graphql")
bond = ZeroCouponBondInput(curve="USD_DISC", maturity=2.0, notional=1_000_000)

# Two-row display: curve + product/risk
await client.stream_curve_and_risk("USD_DISC", bond)
```

Use **stream_realtime_pricing** for single-row NPV/PV01 only. For lower-level control, use **MarketdataClient.subscribe_curve_updates** and **curve_snapshot_to_curve_input**.

## Live blotter

Use **LiveBlotter** and **stream_live_blotter** to show a live-updating table of all products as curve ticks arrive. The blotter handles the ipywidgets layout (title, status, table) and formats numbers (thousands separators, 2 decimals, right-aligned). Requires the jupyter optional dependencies (ipywidgets, pandas).

```python
from IPython.display import display
from pricing_client import (
    LiveBlotter,
    stream_live_blotter,
    PricingClient,
    ZeroCouponBondInput,
    FixedFloatSwapInput,
    FXForwardInput,
    MortgageInput,
    CDSInput,
)

client = PricingClient("http://api:8000/graphql")
# Define products (bond, swap, forward, mortgage, cds) and static curves (eur_curve, hazard_curve, fx_spot_eurusd) as in the demo.

products = [
    ("Zero-coupon bond", bond, lambda c, m: c.price_zero_coupon_bond(bond, m, calculate_pv01=True)),
    ("Fixed-float swap", swap, lambda c, m: c.price_swap(swap, m, calculate_pv01=True)),
    # ... (forward, mortgage, cds)
]

blotter = LiveBlotter(title="Live pricing (USD_DISC)")
display(blotter.widget)

await stream_live_blotter(
    client, blotter, products,
    static_curves=[eur_curve],
    hazard_curves=[hazard_curve],
    fx_spot=[fx_spot_eurusd],
    live_curve_name="USD_DISC",
    max_updates=None,
)
```

See the Jupyter demo notebook (`jupyter/demo.ipynb`) for the full example.

## API

- **hello(name="World")** — Returns greeting string.
- **version()** — Returns API version string.
- **price_zero_coupon_bond(bond, market, calculate_pv01=False, pv01_curve_name=None, pv01_bump_bp=1.0)** — Price a zero-coupon bond. Returns `PricingResult` with `npv` and optional `pv01`.
- **price_swap(swap, market, calculate_pv01=False, pv01_curve_name=None, pv01_bump_bp=1.0)** — Price a fixed-float swap. Returns `PricingResult` with `npv` and optional `pv01`.
- **price_fx_forward(forward, market, calculate_pv01=False, calculate_fx_delta=False, …)** — Price an FX forward (CIP). Returns `PricingResult` with `npv`, optional `pv01` and `fx_delta`.
- **price_mortgage(mortgage, market, calculate_pv01=False, pv01_curve_name=None, pv01_bump_bp=1.0)** — Price a level-pay mortgage. Returns `PricingResult` with `npv` and optional `pv01`.
- **price_cds(cds, market, calculate_cs01=False, cs01_hazard_curve_name=None, cs01_bump_bp=1.0)** — Price a single-name CDS. Returns `PricingResult` with `npv` and optional `cs01`.
- **stream_curve_and_risk(curve_name, bond, marketdata_url, max_updates=None, display=True)** — Stream curve and product/risk in two rows. Row 1: curve; row 2: product + NPV/PV01. Runs until interrupted or `max_updates` if set.
- **stream_realtime_pricing(bond, curve_name, marketdata_url, max_updates=None, display=True)** — Stream real-time NPV/PV01 as curve updates arrive (single row). Runs until interrupted or `max_updates` if set.
- **LiveBlotter(title="Live pricing")** — Display-only widget: `.widget` (VBox to display once), `.update(rows, status_text)` to refresh table and status. Requires ipywidgets and pandas.
- **stream_live_blotter(client, blotter, products, *, static_curves, hazard_curves, fx_spot, live_curve_name, marketdata_url, max_updates)** — Subscribe to live curve, price all products each tick, update the blotter. `products` is a list of `(label, product_input, price_fn)` where `price_fn(client, market)` returns a `PricingResult`.

## Exported types

Use these to build inputs and handle results:

- **CurveInput** — `name`, `pillars`, `zero_rates_cc`, `t0`
- **HazardCurveInput** — `name`, `pillars`, `hazard_rates`, `t0`
- **CurveSnapshot** — curve from marketdata subscription (same shape as CurveInput)
- **CurveUpdate** — `curve` (CurveSnapshot), `rate_deltas_cc`, `rate_deltas_bp` (null for unchanged tenors)
- **FxSpotInput** — `pair`, `spot`
- **MarketInput** — `curves`, `hazard_curves` (optional), `fx_spot` (optional)
- **ZeroCouponBondInput** — `curve`, `maturity`, `notional`
- **FixedFloatSwapInput** — `curve`, `notional`, `fixed_rate`, `pay_times`, `t0`
- **FXForwardInput** — `pair`, `base_curve`, `quote_curve`, `maturity`, `notional_base`, `strike`
- **MortgageInput** — `curve`, `notional`, `annual_rate`, `term_years`, `payments_per_year`
- **CDSInput** — `discount_curve`, `survival_curve`, `notional`, `premium_rate`, `pay_times`, `recovery`, `t0`, `protection_buyer`
- **PricingResult** — `npv`, `pv01` (optional), `fx_delta` (optional), `cs01` (optional)
- **curve_snapshot_to_curve_input(snapshot)** — build CurveInput from CurveSnapshot for pricing API

Example: `from pricing_client import PricingClient, MarketdataClient, LiveBlotter, stream_live_blotter, CurveInput, HazardCurveInput, MarketInput, CDSInput, ZeroCouponBondInput, curve_snapshot_to_curve_input`
