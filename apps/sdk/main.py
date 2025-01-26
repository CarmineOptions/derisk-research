from fastapi import FastAPI, Request, HTTPException
from fastapi.routing import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api.loan_state import loan_router
from api.auth import auth_router
import redis

app = FastAPI()

version = "v1"
version_prefix = f"/api/{version}"

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
app.state.limiter = limiter

@app.middleware("http")
async def rate_limiter_middleware(request: Request, call_next):
    try:
        response = await limiter(request=request, call_next=call_next)
        return response
    except RateLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests. Please try again later."
        )

app.include_router(loan_router, prefix=f"{version_prefix}/loans", tags=["loans"])
app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["auth"])

@app.get("/test")
@limiter.limit("5/minute")
async def test_endpoint(request: Request):
    return {"message": "This is a rate-limited endpoint"}