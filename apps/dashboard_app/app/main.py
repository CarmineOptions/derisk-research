from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from loguru import logger

@asynccontextmanager
async def lifespan(_app: FastAPI):
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log HTTP requests and responses.
    """
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} {request.url}")
    return response


# Example route
@app.get("/")
async def read_root():
    """
    Basic endpoint for testing.
    """
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the FastAPI application!"}


# Additional route
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    logger.info("Health check endpoint accessed.")
    return {"status": "OK"}
