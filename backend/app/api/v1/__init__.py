from fastapi import APIRouter
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.departments import router as departments_router
from backend.app.api.v1.students import router as students_router
from backend.app.api.v1.csv_import import router as csv_import_router
from backend.app.api.v1.predictions import router as predictions_router
from backend.app.api.v1.recommendations import router as recommendations_router
from backend.app.api.v1.assistant import router as assistant_router
from backend.app.api.v1.faculty import router as faculty_router
from backend.app.api.v1.interventions import router as interventions_router
from backend.app.api.v1.admin_analytics import router as admin_analytics_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(departments_router)
api_router.include_router(students_router)
api_router.include_router(csv_import_router)
api_router.include_router(predictions_router)
api_router.include_router(recommendations_router)
api_router.include_router(assistant_router)
api_router.include_router(faculty_router)
api_router.include_router(interventions_router)
api_router.include_router(admin_analytics_router)


