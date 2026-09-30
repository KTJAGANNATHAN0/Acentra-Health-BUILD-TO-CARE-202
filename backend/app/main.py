"""Main FastAPI application for Accentra Fraud Rule Engine."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.engine.registry import load_rules, get_registered_rules
from app.api.transactions import router as transactions_router
from app.api.flags import router as flags_router
from app.api.rules import router as rules_router
from app.api.stats import router as stats_router
from app.api.simulator import router as simulator_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fraud_engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initialize DB and discover pluggable rules on startup."""
    logger.info("Starting up Accentra Fraud Rule Engine...")
    init_db()
    rules = load_rules()
    logger.info(f"Loaded {len(rules)} fraud rules: {[r.name for r in rules]}")
    yield
    logger.info("Shutting down Accentra Fraud Rule Engine...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Fraud Rule Engine with Pluggable Rules and Reviewer Console",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Reviewer Console
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers under /api
app.include_router(transactions_router, prefix="/api")
app.include_router(flags_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(simulator_router, prefix="/api")


@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    """Liveness probe returning system status, registered rules, and notification backend."""
    registered = list(get_registered_rules().keys())
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "rules_registered": registered,
        "notifier": settings.NOTIFIER,
        "flag_threshold": settings.FLAG_THRESHOLD,
        "high_risk_threshold": settings.HIGH_RISK_THRESHOLD
    }
