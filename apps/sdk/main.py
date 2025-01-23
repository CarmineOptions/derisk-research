from fastapi import FastAPI, Request 
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis

app = FastAPI()


redis_client = redis.Redis(host='localhost', port=6379, db=0)
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
@app.get("/test/")
@limiter.limit("1/second")  
async def test_endpoint(request: Request):  
    return {"message": "This is a test endpoint"}

@app.get("/debug/rate-limit")
async def debug_rate_limit(request: Request):
    
    client_ip = get_remote_address(request)
    key = f"rate_limit:{client_ip}"
    remaining_requests = redis_client.get(key)
    return {
        "client_ip": client_ip,
        "remaining_requests": int(remaining_requests) if remaining_requests else "No limit set"
    }

@app.get("/health/")
async def health_check():
    return {"status": "ok"}