from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from loguru import logger

from app.api import watcher


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
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(watcher.router)


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


# Example route
@app.get("/")
async def read_root() -> dict[str, str]:
    """
    Basic endpoint for testing.
    """
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the FastAPI application!"}


# Additional route
@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """
    logger.info("Health check endpoint accessed.")
    return {"status": "OK"}
