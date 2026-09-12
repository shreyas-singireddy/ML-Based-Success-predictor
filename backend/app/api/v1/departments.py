from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_roles
from backend.app.models.user import User, UserRole
from backend.app.models.department import Department
from backend.app.schemas.department import DepartmentCreate, DepartmentResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Department).order_by(Department.code.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_in: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    stmt = select(Department).where(Department.code == dept_in.code.upper().strip())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Department with code '{dept_in.code}' already exists."
        )

    dept = Department(
        code=dept_in.code.upper().strip(),
        name=dept_in.name.strip()
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept
