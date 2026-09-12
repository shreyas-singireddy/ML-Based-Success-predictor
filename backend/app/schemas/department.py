import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=20, example="CS")
    name: str = Field(..., min_length=2, max_length=100, example="Computer Science & Engineering")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
