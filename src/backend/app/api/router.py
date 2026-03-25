from fastapi import APIRouter

from app.api.analytics import router as analytics_router
from app.api.assessments import router as assessments_router
from app.api.auth import router as auth_router
from app.api.competencies import router as competencies_router
from app.api.departments import router as departments_router
from app.api.development_plans import router as development_plans_router
from app.api.export import router as export_router
from app.api.imports import router as imports_router
from app.api.system import router as system_router
from app.api.target_profiles import router as target_profiles_router
from app.api.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(system_router)
api_router.include_router(departments_router)
api_router.include_router(users_router)
api_router.include_router(competencies_router)
api_router.include_router(target_profiles_router)
api_router.include_router(assessments_router)
api_router.include_router(analytics_router)
api_router.include_router(development_plans_router)
api_router.include_router(export_router)
api_router.include_router(imports_router)
