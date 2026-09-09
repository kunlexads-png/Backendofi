import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import engine, Base
from app.routes import (
    auth_router,
    users_router,
    arrival_router,
    finished_goods_router,
    byproduct_router,
    stock_router,
    uploads_router,
    dashboard_router,
    ai_assistant_router,
    reports_router,
)

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ofi_warehouse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown hooks.
    Ensures database tables are initialized if migrations haven't run yet.
    """
    logger.info("Initializing OFI Cocoa Warehouse Backend...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield
    logger.info("Shutting down OFI Cocoa Warehouse Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-ready backend for the OFI Cocoa Warehouse AI Assistant. "
        "Provides Cocoa Arrival Tracking, Finished Goods Warehouse, By-Product Management, "
        "Centralized Stock Ledger, File Upload Parsing, Executive Dashboards, and Gemini-Powered AI Assistant."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized Exception Handlers (Standard React-friendly JSON format)
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "data": None,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "details": exc.detail
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({
            "field": field,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Request validation failed",
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "details": errors
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred. Please contact the warehouse administrator.",
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "details": None  # Never leak internal stack trace to end users
            }
        }
    )


# Health Check
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    return {
        "success": True,
        "message": "OFI Cocoa Warehouse Backend is online and operational",
        "data": {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "environment": "production"
        },
        "error": None
    }


# Mount Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(arrival_router, prefix=settings.API_V1_STR)
app.include_router(finished_goods_router, prefix=settings.API_V1_STR)
app.include_router(byproduct_router, prefix=settings.API_V1_STR)
app.include_router(stock_router, prefix=settings.API_V1_STR)
app.include_router(uploads_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(ai_assistant_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
