from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import logging

from app.database.db import Base, engine
from app.models.product import Product
from app.models.user import User
from app.models.order import Order
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile
from app.models.conversation_summary import ConversationSummary
from app.routers import assistant
from app.routers import auth, products, orders
from app.routers import scanner
from app.routers import knowledge
from app.routers import rag
from app.routers import farm_plan
from app.routers import voice, analytics
from app.models.farm_plan import FarmPlan

# Import production features
from app.core.logging_config import setup_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.config import CORS_ORIGINS, ENVIRONMENT, LOG_DIR
from app.core.health import HealthChecker
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# Initialize logging
setup_logging(LOG_DIR)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KrishiSathi-VikasBeejBhandar",
    description="Agricultural E-commerce Platform",
    version="1.0.0",
    docs_url="/api/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if ENVIRONMENT == "development" else None,
)

# Create tables
Base.metadata.create_all(bind=engine)

os.makedirs(LOG_DIR, exist_ok=True)

logger.info(f"Starting KrishiSathi application in {ENVIRONMENT} environment")

# ============================================================
# EXCEPTION HANDLERS
# ============================================================
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ============================================================
# MIDDLEWARE
# ============================================================

# Request/Response logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - Production-safe configuration
allowed_origins = [origin.strip() for origin in CORS_ORIGINS]
logger.info(f"Configured CORS origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Mount uploads static folder
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

# ============================================================
# HEALTH & MONITORING ENDPOINTS
# ============================================================

@app.get("/api/health")
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return await HealthChecker.get_full_health()


@app.get("/api/health/ready")
async def readiness_check():
    """Readiness check - can app handle requests?"""
    db_health = await HealthChecker.get_database_health()
    if db_health["status"] != "healthy":
        return {"status": "not_ready", "reason": "Database unavailable"}
    return {"status": "ready"}


@app.get("/api/health/live")
async def liveness_check():
    """Liveness check - is app running?"""
    return {"status": "alive", "environment": ENVIRONMENT}

# ============================================================
# API ROUTERS
# ============================================================

# Authentication
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["auth"]
)

# Scanner
app.include_router(
    scanner.router,
    prefix="/api/scanner",
    tags=["Scanner"]
)

# Products
app.include_router(
    products.router,
    prefix="/api/products",
    tags=["products"]
)

# Orders
app.include_router(
    orders.router,
    prefix="/api/orders",
    tags=["orders"]
)

# Knowledge Base
app.include_router(
    knowledge.router,
    prefix="/api/knowledge",
    tags=["Knowledge Base"]
)

# RAG
app.include_router(
    rag.router,
    prefix="/api/rag",
    tags=["RAG"]
)

# Farm Planning
app.include_router(
    farm_plan.router
)

# Voice
app.include_router(
    voice.router
)

# Assistant
app.include_router(
    assistant.router
)

# Analytics
app.include_router(
    analytics.router
)

# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    """Root endpoint - application status"""
    return {
        "message": "KrishiSathi-VikasBeejBhandar is Running",
        "status": "ok",
        "environment": ENVIRONMENT,
        "version": "1.0.0",
        "docs": "/api/docs" if ENVIRONMENT == "development" else None
    }


# ============================================================
# STARTUP & SHUTDOWN EVENTS
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info(f"Application startup in {ENVIRONMENT} environment")
    logger.info(f"CORS origins configured: {CORS_ORIGINS}")
    logger.info("All routers initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("Application shutdown")



