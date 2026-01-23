"""
OpenHeart Cyprus - FastAPI Application Entry Point.

A GDPR-compliant Cardiology EMR for Cypriot cardiologists.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
from fastapi import FastAPI, Request
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import settings
from app.core.audit import AuditMiddleware
from app.db.session import engine

# Import all models to ensure SQLAlchemy mapper resolution works
import app.integrations.dicom.mwl_models  # noqa: F401 - ScheduledProcedure for Patient relationship

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Initialize Redis connection pool
    app.state.redis = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )

    # Verify database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

    # Verify Redis connection
    try:
        await app.state.redis.ping()
        logger.info("Redis connection verified")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

    # Seed development data (guarded: only runs in dev with empty DB)
    if settings.environment == "development":
        try:
            from app.core.seed import run_seed
            await run_seed()
        except Exception as e:
            logger.warning(f"Development seed failed (non-fatal): {e}")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await app.state.redis.close()
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Open-source Cardiology EMR for Cypriot cardiologists. "
    "GDPR-compliant with Gesy integration, FHIR R4 interoperability, "
    "and DICOM imaging support.",
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# =============================================================================
# Middleware
# =============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# GDPR Audit Logging
app.add_middleware(AuditMiddleware)


# =============================================================================
# Health Check Endpoints
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check(request: Request) -> dict:
    """
    Health check endpoint for container orchestration.

    Returns status of all dependent services.
    """
    checks: dict[str, bool | str] = {}

    # Database check
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database"] = f"Error: {str(e)}"

    # Redis check
    try:
        await request.app.state.redis.ping()
        checks["redis"] = True
    except Exception as e:
        checks["redis"] = f"Error: {str(e)}"

    # Orthanc check (non-critical)
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.orthanc_url}/system",
                auth=(settings.orthanc_username, settings.orthanc_password),
            )
            checks["orthanc"] = response.status_code == 200
    except Exception:
        checks["orthanc"] = "unavailable"

    # Determine overall health
    critical_services = ["database", "redis"]
    all_healthy = all(
        checks.get(svc) is True for svc in critical_services
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": checks,
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Cardiology EMR for Cyprus",
        "docs": "/docs" if not settings.is_production else None,
        "health": "/health",
    }


# =============================================================================
# Include Routers
# =============================================================================

# Import implemented routers
from app.modules.auth.router import router as auth_router
from app.modules.cardiology.cdss.router import router as cdss_router
from app.modules.notes.router import router as notes_router
from app.modules.patient.router import router as patient_router
from app.modules.encounter.router import router as encounter_router

# Include implemented routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])
app.include_router(cdss_router, prefix="/api", tags=["CDSS"])
app.include_router(notes_router, prefix="/api", tags=["Clinical Notes"])
app.include_router(patient_router, prefix="/api", tags=["Patients"])
app.include_router(encounter_router, prefix="/api", tags=["Encounters"])

# DICOM Integration
from app.integrations.dicom.router import router as dicom_router
from app.integrations.dicom.mwl_router import router as mwl_router
app.include_router(dicom_router, prefix="/api", tags=["DICOM/Imaging"])
app.include_router(mwl_router, prefix="/api", tags=["Modality Worklist"])

# Gesy Integration
from app.integrations.gesy.router import router as gesy_router
app.include_router(gesy_router, prefix="/api", tags=["Gesy"])

# Medical Coding
from app.modules.coding.router import router as coding_router
app.include_router(coding_router, prefix="/api", tags=["Medical Coding"])

# Appointments
from app.modules.appointment.router import router as appointment_router
app.include_router(appointment_router, prefix="/api", tags=["Appointments"])

# Routers to be implemented:
# from app.integrations.fhir.router import router as fhir_router
# app.include_router(fhir_router, prefix="/fhir/r4", tags=["FHIR"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
