import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from backend.app.models.student import GenderEnum
from backend.app.schemas.academic_record import AcademicRecordCreate, AcademicRecordResponse


class StudentBase(BaseModel):
    student_number: str = Field(..., min_length=2, max_length=50, example="STU-2024-001")
    name: str = Field(..., min_length=2, max_length=150, example="Alice Johnson")
    gender: GenderEnum = Field(default=GenderEnum.OTHER, example=GenderEnum.FEMALE)
    age: int = Field(..., ge=15, le=100, example=20)
    department_id: uuid.UUID = Field(..., description="Foreign key to departments.id")
    enrollment_year: int = Field(..., ge=2000, le=2100, example=2023)
    current_semester: int = Field(..., ge=1, le=12, example=4)
    cumulative_gpa: Optional[float] = Field(None, ge=0.0, le=10.0, example=8.45)
    total_credits_earned: int = Field(0, ge=0, example=64)


class StudentCreate(StudentBase):
    initial_academic_record: Optional[AcademicRecordCreate] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    gender: Optional[GenderEnum] = None
    age: Optional[int] = Field(None, ge=15, le=100)
    department_id: Optional[uuid.UUID] = None
    enrollment_year: Optional[int] = Field(None, ge=2000, le=2100)
    current_semester: Optional[int] = Field(None, ge=1, le=12)
    cumulative_gpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    total_credits_earned: Optional[int] = Field(None, ge=0)
    is_archived: Optional[bool] = None


class StudentResponse(StudentBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentDetailResponse(StudentResponse):
    academic_records: List[AcademicRecordResponse] = []


class StudentListResponse(BaseModel):
    items: List[StudentResponse]
    total: int
    page: int
    limit: int
    pages: int
