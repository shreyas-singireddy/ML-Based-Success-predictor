from fastapi import APIRouter
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.departments import router as departments_router
from backend.app.api.v1.students import router as students_router
from backend.app.api.v1.csv_import import router as csv_import_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(departments_router)
api_router.include_router(students_router)
api_router.include_router(csv_import_router)
