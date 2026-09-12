import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_roles, verify_student_access
from backend.app.models.user import User, UserRole
from backend.app.models.student import StudentProfile
from backend.app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDetailResponse,
    StudentListResponse
)
from backend.app.schemas.academic_record import (
    AcademicRecordCreate,
    AcademicRecordUpdate,
    AcademicRecordResponse
)
from backend.app.services.student_service import StudentService
from backend.app.services.academic_service import AcademicService

router = APIRouter(prefix="/students", tags=["Students"])


def _map_student_response(student: StudentProfile) -> StudentResponse:
    dept_code = student.department.code if student.department else None
    dept_name = student.department.name if student.department else None
    return StudentResponse(
        id=student.id,
        user_id=student.user_id,
        student_number=student.student_number,
        name=student.name,
        gender=student.gender,
        age=student.age,
        department_id=student.department_id,
        department_code=dept_code,
        department_name=dept_name,
        enrollment_year=student.enrollment_year,
        current_semester=student.current_semester,
        cumulative_gpa=float(student.cumulative_gpa) if student.cumulative_gpa is not None else None,
        total_credits_earned=student.total_credits_earned,
        is_archived=student.is_archived,
        created_at=student.created_at,
        updated_at=student.updated_at
    )


def _map_student_detail(student: StudentProfile) -> StudentDetailResponse:
    base = _map_student_response(student)
    records = [
        AcademicRecordResponse(
            id=r.id,
            student_id=r.student_id,
            academic_year=r.academic_year,
            semester=r.semester,
            attendance_percentage=float(r.attendance_percentage),
            previous_cgpa=float(r.previous_cgpa) if r.previous_cgpa is not None else None,
            mid_1=float(r.mid_1) if r.mid_1 is not None else None,
            mid_2=float(r.mid_2) if r.mid_2 is not None else None,
            internal_marks=float(r.internal_marks) if r.internal_marks is not None else None,
            backlogs=r.backlogs,
            semester_cgpa=float(r.semester_cgpa) if r.semester_cgpa is not None else None,
            grade=r.grade,
            historical_risk_level=r.historical_risk_level,
            notes=r.notes,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in (student.academic_records or [])
    ]
    return StudentDetailResponse(
        **base.model_dump(),
        academic_records=records
    )


@router.get("", response_model=StudentListResponse)
async def list_students(
    search: Optional[str] = Query(None, description="Search by student ID or name"),
    department_id: Optional[uuid.UUID] = Query(None, description="Filter by department"),
    semester: Optional[int] = Query(None, ge=1, le=12, description="Filter by current semester"),
    is_archived: bool = Query(False, description="Filter active vs archived"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    items, total = await StudentService.get_students(
        db=db,
        search=search,
        department_id=department_id,
        semester=semester,
        is_archived=is_archived,
        page=page,
        limit=limit
    )
    pages = (total + limit - 1) // limit if total > 0 else 1
    return StudentListResponse(
        items=[_map_student_response(s) for s in items],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.post("", response_model=StudentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_in: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    student = await StudentService.create_student(db, student_in)
    # Reload complete student details
    full_student = await StudentService.get_student_by_id(db, student.id)
    return _map_student_detail(full_student)


@router.get("/{student_id}", response_model=StudentDetailResponse)
async def get_student_profile(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student: StudentProfile = Depends(verify_student_access)
):
    full_student = await StudentService.get_student_by_id(db, student_id)
    return _map_student_detail(full_student)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: uuid.UUID,
    student_in: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    updated = await StudentService.update_student(db, student_id, student_in)
    return _map_student_response(updated)


@router.delete("/{student_id}", response_model=StudentResponse)
async def archive_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    archived = await StudentService.archive_student(db, student_id)
    return _map_student_response(archived)


@router.post("/{student_id}/restore", response_model=StudentResponse)
async def restore_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    restored = await StudentService.restore_student(db, student_id)
    return _map_student_response(restored)


@router.get("/{student_id}/academic-history", response_model=List[AcademicRecordResponse])
async def get_academic_history(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student: StudentProfile = Depends(verify_student_access)
):
    records = await AcademicService.get_student_academic_history(db, student_id)
    return [
        AcademicRecordResponse(
            id=r.id,
            student_id=r.student_id,
            academic_year=r.academic_year,
            semester=r.semester,
            attendance_percentage=float(r.attendance_percentage),
            previous_cgpa=float(r.previous_cgpa) if r.previous_cgpa is not None else None,
            mid_1=float(r.mid_1) if r.mid_1 is not None else None,
            mid_2=float(r.mid_2) if r.mid_2 is not None else None,
            internal_marks=float(r.internal_marks) if r.internal_marks is not None else None,
            backlogs=r.backlogs,
            semester_cgpa=float(r.semester_cgpa) if r.semester_cgpa is not None else None,
            grade=r.grade,
            historical_risk_level=r.historical_risk_level,
            notes=r.notes,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in records
    ]


@router.post("/{student_id}/academic-records", response_model=AcademicRecordResponse, status_code=status.HTTP_201_CREATED)
async def add_academic_record(
    student_id: uuid.UUID,
    record_in: AcademicRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    record = await AcademicService.create_academic_record(db, student_id, record_in)
    return AcademicRecordResponse(
        id=record.id,
        student_id=record.student_id,
        academic_year=record.academic_year,
        semester=record.semester,
        attendance_percentage=float(record.attendance_percentage),
        previous_cgpa=float(record.previous_cgpa) if record.previous_cgpa is not None else None,
        mid_1=float(record.mid_1) if record.mid_1 is not None else None,
        mid_2=float(record.mid_2) if record.mid_2 is not None else None,
        internal_marks=float(record.internal_marks) if record.internal_marks is not None else None,
        backlogs=record.backlogs,
        semester_cgpa=float(record.semester_cgpa) if record.semester_cgpa is not None else None,
        grade=record.grade,
        historical_risk_level=record.historical_risk_level,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at
    )


@router.put("/{student_id}/academic-records/{record_id}", response_model=AcademicRecordResponse)
async def update_academic_record(
    student_id: uuid.UUID,
    record_id: uuid.UUID,
    record_in: AcademicRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    record = await AcademicService.update_academic_record(db, record_id, record_in)
    return AcademicRecordResponse(
        id=record.id,
        student_id=record.student_id,
        academic_year=record.academic_year,
        semester=record.semester,
        attendance_percentage=float(record.attendance_percentage),
        previous_cgpa=float(record.previous_cgpa) if record.previous_cgpa is not None else None,
        mid_1=float(record.mid_1) if record.mid_1 is not None else None,
        mid_2=float(record.mid_2) if record.mid_2 is not None else None,
        internal_marks=float(record.internal_marks) if record.internal_marks is not None else None,
        backlogs=record.backlogs,
        semester_cgpa=float(record.semester_cgpa) if record.semester_cgpa is not None else None,
        grade=record.grade,
        historical_risk_level=record.historical_risk_level,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at
    )
