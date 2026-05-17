"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, auth, news, payments, signals, subscriptions
from app.core.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    version=settings.app_version,
    description="Smart Metals & FX Intelligence System — 8 analytical schools fused with AI.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "endpoints": [
            "POST /api/auth/register",
            "POST /api/auth/login",
            "POST /api/signals/generate",
            "GET  /api/signals/latest",
            "GET  /api/analysis/{symbol}",
            "GET  /api/news/upcoming",
            "GET  /api/subscriptions/plans",
            "POST /api/payments/checkout",
            "POST /api/payments/webhook",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(signals.router)
app.include_router(analysis.router)
app.include_router(news.router)
app.include_router(subscriptions.router)
app.include_router(payments.router)
