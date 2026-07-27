"""FastAPI application entry point (Sprint 6, Day 38).

Run:  uvicorn src.api.main:app --port 8000
Docs: http://localhost:8000/docs
"""

import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .db import APP_VERSION, get_connection  # noqa: F401 (re-exported for convenience)

load_dotenv()

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    version=APP_VERSION,
    description="REST API over the Nifty 100 financial analytics platform.",
)

# CORS — internal-use tool, allow all origins per spec
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs method, path, and response time for every request."""
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    print(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


# ---- Routers (imported with the /api/v1 prefix) ----
from .routers import (
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
    health,
)  # noqa: E402

app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
