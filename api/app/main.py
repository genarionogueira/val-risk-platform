"""FastAPI app with Strawberry GraphQL."""

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.schema import schema

app = FastAPI(title="Pricing API", version="0.1.0")
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check for load balancers and Docker."""
    return {"status": "ok"}
