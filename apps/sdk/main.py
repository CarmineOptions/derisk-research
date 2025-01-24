from fastapi import FastAPI
from api.loan_state import loan_router

app = FastAPI()

version = "v1"
version_prefix = f"/api/{version}"


app.include_router(loan_router, prefix=f"{version_prefix}/loans", tags=["loans"])
