# Pricing API

FastAPI + Strawberry GraphQL service that exposes the pricing library. Quants can submit trade definitions and market snapshots and receive pricing and risk (NPV, PV01, FX delta) from the library.

## Endpoints

- **GET /health** — Health check (for load balancers and Docker).
- **POST /graphql** — GraphQL endpoint. Playground available at http://localhost:8000/graphql in the browser.

## Local development

From the repo root, install the API and the pricing library (path dependency):

```bash
cd api
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/graphql for the GraphQL Playground.

## Docker

The API Dockerfile installs the pricing library from the mounted or copied `pricing-library` directory. Use Docker Compose from the repo root:

```bash
docker-compose up api
```

When run via docker-compose, the API is served by **api-backend** with replicas defined in the compose file (`deploy.replicas: 3`). **Traefik** (service name `api`, port 8000) load-balances across all replicas. Clients and Jupyter use `http://api:8000` as before.

## GraphQL schema

### Queries

- **hello(name: String = "World"): String** — Hello-world placeholder.
- **version: String** — API version.
- **priceZeroCouponBond(bond, market, calculatePv01?, …): PricingResult** — Price a zero-coupon bond; optionally compute PV01.
- **priceSwap(swap, market, calculatePv01?, …): PricingResult** — Price a fixed-float swap; optionally compute PV01.
- **priceFxForward(forward, market, calculatePv01?, calculateFxDelta?, …): PricingResult** — Price an FX forward; optionally PV01 and FX delta.
- **priceMortgage(mortgage, market, calculatePv01?, …): PricingResult** — Price a level-pay mortgage; optionally compute PV01.

### Input types

- **MarketInput** — `curves: [CurveInput!]!`, `fxSpot: [FxSpotInput]` (optional).
- **CurveInput** — `name`, `pillars: [Float!]!`, `zeroRatesCc: [Float!]!`, `t0` (default 0).
- **FxSpotInput** — `pair`, `spot`.
- **ZeroCouponBondInput** — `curve`, `maturity`, `notional`.
- **FixedFloatSwapInput** — `curve`, `notional`, `fixedRate`, `payTimes`, `t0` (default 0).
- **FXForwardInput** — `pair`, `quoteCurve`, `maturity`, `notionalBase`, `strike`.
- **MortgageInput** — `curve`, `notional`, `annualRate`, `termYears`, `paymentsPerYear`.

### Output types

- **PricingResult** — `npv: Float!`, `riskMeasures: RiskMeasures` (optional).
- **RiskMeasures** — `pv01: Float`, `fxDelta: Float`.

Times are in **year fractions**; rates are **continuously compounded**. All pricing and risk logic is delegated to the pricing library.

## Example: Zero-coupon bond

Price a 2Y zero-coupon bond for 1,000,000 USD and request PV01 (1 bp parallel curve bump):

```graphql
query PriceZCB {
  priceZeroCouponBond(
    bond: {
      curve: "USD_DISC"
      maturity: 2.0
      notional: 1000000
    }
    market: {
      curves: [{
        name: "USD_DISC"
        pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
        zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037]
      }]
    }
    calculatePv01: true
  ) {
    npv
    riskMeasures {
      pv01
    }
  }
}
```

Example response (matches pricing-library demo):

```json
{
  "data": {
    "priceZeroCouponBond": {
      "npv": 923116.35,
      "riskMeasures": {
        "pv01": -184.60
      }
    }
  }
}
```

## Example: Fixed-float swap

```graphql
query PriceSwap {
  priceSwap(
    swap: {
      curve: "USD_DISC"
      notional: 10000000
      fixedRate: 0.04
      payTimes: [0.5, 1.0, 1.5, 2.0]
    }
    market: {
      curves: [{
        name: "USD_DISC"
        pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
        zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037]
      }]
    }
    calculatePv01: true
  ) {
    npv
    riskMeasures { pv01 }
  }
}
```

## Example: FX forward (with FX delta)

```graphql
query PriceFXForward {
  priceFxForward(
    forward: {
      pair: "EURUSD"
      quoteCurve: "USD_DISC"
      maturity: 1.0
      notionalBase: 5000000
      strike: 1.085
    }
    market: {
      curves: [{
        name: "USD_DISC"
        pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
        zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037]
      }]
      fxSpot: [{ pair: "EURUSD", spot: 1.08 }]
    }
    calculatePv01: true
    calculateFxDelta: true
  ) {
    npv
    riskMeasures { pv01 fxDelta }
  }
}
```

## Error handling

Invalid inputs (e.g. missing curve in market, negative maturity, empty pay times) return GraphQL errors with descriptive messages. The API does not crash; errors are returned in the `errors` array of the response.

## Tests

From the `api` directory:

```bash
poetry run pytest tests/ -v
```
