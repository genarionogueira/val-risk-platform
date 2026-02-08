# Marketdata GraphQL Service

GraphQL service for curve data: **query** a curve by name and **subscribe** to curve updates streamed in real time via Redis.

## Run

From the repo root:

```bash
cd marketdata
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Use port 8001 so the pricing API can stay on 8000 when both run locally. Set `REDIS_URL` if Redis is not at `redis://localhost:6379/0`.

**Docker:** From the repo root, `docker compose up` starts Redis and the marketdata service (marketdata depends on Redis and uses `REDIS_URL=redis://redis:6379/0`).

- **Health:** http://localhost:8001/health  
- **GraphQL:** http://localhost:8001/graphql  

## Redis streaming queue

- **Redis** is used as a streaming queue. Curve updates are written to **Redis Streams** (one stream per curve: `curve_updates:{curve_name}`).
- A **simulated feed** (background task) runs inside the marketdata service: every 2 seconds it applies a small rate delta to the sample curve (USD_DISC), updates the in-memory store, and **XADD**s a full curve snapshot to the stream.
- The **subscription** `curveUpdated(name)` yields the current curve once from the store, then **XREAD**s from the stream and yields each new update to the client in real time.

## Schema

- **Query**
  - `curve(name: String!): Curve` — Returns the curve for the given name, or `null` if not found.

- **Subscription**
  - `curveUpdated(name: String!): Curve` — Subscribe to curve updates by name. Yields the current curve once, then streams each update from Redis (simulated feed pushes to the stream every ~2 seconds for USD_DISC).

- **Curve** type: `name`, `pillars`, `zeroRatesCc`, `t0` (same shape as the pricing library).

## Example query

```graphql
query {
  curve(name: "USD_DISC") {
    name
    pillars
    zeroRatesCc
    t0
  }
}
```

## Subscriptions

Subscriptions use WebSocket on the same `/graphql` path. Use a client that supports GraphQL over WebSocket (e.g. graphql-ws or GraphiQL with subscriptions) and subscribe to `curveUpdated(name: "USD_DISC")`. You receive the current curve first, then a new Curve event every ~2 seconds as the simulated feed publishes to Redis.
