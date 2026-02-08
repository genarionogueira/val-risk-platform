"""FastAPI app with Strawberry GraphQL (query + subscription)."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.feed import run_feed
from app.redis_client import close_redis, get_redis
from app.schema import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start simulated feed task and close Redis on shutdown."""
    redis = await get_redis()
    feed_task = asyncio.create_task(run_feed())
    try:
        yield
    finally:
        feed_task.cancel()
        try:
            await feed_task
        except asyncio.CancelledError:
            pass
        await close_redis()


app = FastAPI(title="Marketdata API", version="0.1.0", lifespan=lifespan)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check for load balancers and Docker."""
    return {"status": "ok"}
