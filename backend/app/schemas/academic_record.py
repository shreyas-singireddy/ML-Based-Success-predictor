import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class AcademicRecordBase(BaseModel):
    academic_year: str = Field(
        ...,
        pattern=r"^\d{4}-\d{4}$",
        description="Academic year in format YYYY-YYYY (e.g. 2024-2025)",
        example="2024-2025"
    )
    semester: int = Field(..., ge=1, le=12, description="Semester index between 1 and 12", example=4)
    attendance_percentage: float = Field(..., ge=0.0, le=100.0, description="Attendance percentage 0.00-100.00", example=85.5)
    previous_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0, description="Previous cumulative GPA", example=7.8)
    mid_1: Optional[float] = Field(None, ge=0.0, le=100.0, description="Mid 1 score 0.00-100.00", example=78.0)
    mid_2: Optional[float] = Field(None, ge=0.0, le=100.0, description="Mid 2 score 0.00-100.00", example=82.5)
    internal_marks: Optional[float] = Field(None, ge=0.0, le=100.0, description="Internal assessment marks", example=80.0)
    backlogs: int = Field(0, ge=0, description="Non-negative backlog count", example=0)
    semester_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0, description="Actual recorded term CGPA", example=8.1)
    grade: Optional[str] = Field(None, max_length=10, description="Official letter grade", example="A")
    historical_risk_level: Optional[str] = Field(
        None,
        max_length=20,
        description="Temporary Phase-1 legacy/imported risk field. Dynamic ML risk is stored in predictions."
    )
    notes: Optional[str] = Field(None, description="Optional advisor notes")

    @field_validator("academic_year")
    @classmethod
    def validate_year_sequence(cls, v: str) -> str:
        parts = v.split("-")
        if len(parts) == 2:
            try:
                y1, y2 = int(parts[0]), int(parts[1])
                if y2 != y1 + 1:
                    raise ValueError(f"Academic year second year must be consecutive (got {v})")
            except ValueError as e:
                raise ValueError(str(e))
        return v


class AcademicRecordCreate(AcademicRecordBase):
    pass


class AcademicRecordUpdate(BaseModel):
    attendance_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    previous_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    mid_1: Optional[float] = Field(None, ge=0.0, le=100.0)
    mid_2: Optional[float] = Field(None, ge=0.0, le=100.0)
    internal_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    backlogs: Optional[int] = Field(None, ge=0)
    semester_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    grade: Optional[str] = None
    historical_risk_level: Optional[str] = None
    notes: Optional[str] = None


class AcademicRecordResponse(AcademicRecordBase):
    id: uuid.UUID
    student_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
