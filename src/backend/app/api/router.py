from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.departments import router as departments_router
from app.api.system import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(system_router)
api_router.include_router(departments_router)
