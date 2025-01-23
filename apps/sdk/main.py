from fastapi import FastAPI
from typing import Dict

import redis.asyncio as redis
from fastapi import Depends, FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    """
    Initialize rate limiter with Redis on application startup.
    
    This function runs when the FastAPI application starts and:
    1. Establishes connection to Redis
    2. Initializes the FastAPI rate limiter
    
    Note:
        Requires a running Redis instance at redis://redis:6379/0
    
    Returns:
        None
    """
    redis_instance = redis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True
    )
    await FastAPILimiter.init(redis_instance)

@app.get(
    "/test-rate-limit",
    dependencies=[Depends(RateLimiter(times=2, seconds=5))],
    response_model=Dict[str, str]
)
async def test_rate_limit() -> Dict[str, str]:
    """
    Test endpoint for debugging and demonstrating rate limiting functionality.
    
    This endpoint is protected by a rate limiter that allows:
    - Maximum 2 requests
    - Within a 5 second window
    - Per unique client (identified by IP address)
    
    After the limit is reached, subsequent requests will receive a 429 status code
    until the time window expires.
    
    Returns:
        Dict[str, str]: A dictionary containing success message and rate limit details
        
    Raises:
        HTTPException: 429 Too Many Requests when rate limit is exceeded
    """
    return {
        "message": "Rate limit test successful",
        "details": "This endpoint is limited to 2 requests per 5 seconds"
    }


