from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable, Any
import os

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger

from dashboard_app.app.api import watcher
from dashboard_app.app.api import telegram
from dashboard_app.app.api import history
from dashboard_app.app.api import auth
from dashboard_app.app.api import loan_state


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    """
    Lifespan event handler for the FastAPI application.
    This asynchronous generator function handles the startup and shutdown events
    of the FastAPI application. It performs necessary initialization when the app
    starts and cleanup when the app shuts down.
    Args:
        _app (FastAPI): The FastAPI application instance.
    Yields:
        None: This function yields control back to the FastAPI event loop.
    """

    # Code to run when the app starts.
    # For example, database connection setup or loading configurations.
    logger.info("Application startup: Initializing resources.")

    yield

    # Code to run when the app shuts down.
    # For example, closing database connections or cleaning up.
    logger.info("Application shutdown: Cleaning up resources.")


# Initialize FastAPI app
app = FastAPI(lifespan=lifespan, root_path="/api")
# Load allowed CORS origins from environment variable, default to Vite dev server
origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="dashboard_app/app/static"), name="static")
app.include_router(watcher.router)
app.include_router(history.router)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(loan_state.router, prefix="/api/v1/loans", tags=["loans"])
app.include_router(telegram.router)


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware to log HTTP requests and responses.
    """
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} {request.url}")
    return response


# Example route: lists core features, including the new notification subscription
@app.get("/", response_model=dict[str, Any])
async def read_root() -> dict[str, Any]:
    """
    Root endpoint detailing available features of the Dashboard API.
    """
    logger.info("Root endpoint accessed.")
    return {
        "message": "Welcome to the DeRisk Dashboard API",
        "features": [
            "Interactive data visualization",
            "Protocol statistics monitoring",
            "Loan portfolio analysis",
            "Real-time data updates",
            "Notification subscription via POST /api/liquidation-watcher",
            "Telegram OAuth authentication via POST /api/auth/telegram-oauth",
        ],
    }


# Health check endpoint extended with service info
@app.get("/health", response_model=dict[str, Any])
async def health_check() -> dict[str, Any]:
    """
    Simple health check endpoint for liveness.
    """
    logger.info("Health check endpoint accessed.")
    return {"status": "OK", "service": "dashboard_app_api"}
