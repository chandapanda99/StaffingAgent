from app.api.routes import health, workflows
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workflows.router, tags=["workflows"])
