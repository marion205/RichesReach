# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from settings import settings
from schema import schema
from observability import observe
from prometheus_client import make_asgi_app

app = FastAPI(title="RichesReach", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# Attach user to context (mock); replace with real auth
@app.middleware("http")
async def attach_user(request: Request, call_next):
    request.state.user = {
        "email": "test@example.com",
        "incomeProfile": {
            "incomeBracket": "Under $30,000",
            "age": 28,
            "investmentGoals": ["Emergency Fund","Wealth Building"],
            "riskTolerance": "Moderate",
            "investmentHorizon": "5-10 years",
        },
        "liquidCashUSD": 1800,   # drives suitability
        "monthlyContributionUSD": 150
    }
    with observe(route=request.url.path):
        response = await call_next(request)
        return response

@app.get("/health")
async def health():
    return {"status":"ok","schemaVersion": settings.SCHEMA_VERSION}

app.mount("/metrics", make_asgi_app())

app.add_route(
    "/graphql", GraphQLApp(schema=schema, on_get=make_graphiql_handler())
)
