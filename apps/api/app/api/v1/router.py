"""Root router for API v1."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, challenges, health, progress

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(challenges.router)
api_v1_router.include_router(progress.router)
