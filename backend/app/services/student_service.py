import uuid
from typing import Optional, Tuple, List
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.student import StudentProfile
from backend.app.models.department import Department
from backend.app.models.academic_record import SemesterAcademicRecord
from backend.app.schemas.student import StudentCreate, StudentUpdate


class StudentService:
    @staticmethod
    async def create_student(db: AsyncSession, student_in: StudentCreate) -> StudentProfile:
        # 1. Check Student Number Uniqueness
        stmt = select(StudentProfile).where(StudentProfile.student_number == student_in.student_number.strip())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student with ID '{student_in.student_number}' already exists."
            )

        # 2. Check Department Existence
        dept = await db.get(Department, student_in.department_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID '{student_in.department_id}' not found."
            )

        # 3. Create Student Profile
        student = StudentProfile(
            student_number=student_in.student_number.strip(),
            name=student_in.name.strip(),
            gender=student_in.gender,
            age=student_in.age,
            department_id=student_in.department_id,
            enrollment_year=student_in.enrollment_year,
            current_semester=student_in.current_semester,
            cumulative_gpa=student_in.cumulative_gpa,
            total_credits_earned=student_in.total_credits_earned,
            is_archived=False
        )
        db.add(student)
        await db.flush()

        # 4. Optional Initial Academic Record
        if student_in.initial_academic_record:
            rec_in = student_in.initial_academic_record
            record = SemesterAcademicRecord(
                student_id=student.id,
                academic_year=rec_in.academic_year,
                semester=rec_in.semester,
                attendance_percentage=rec_in.attendance_percentage,
                previous_cgpa=rec_in.previous_cgpa,
                mid_1=rec_in.mid_1,
                mid_2=rec_in.mid_2,
                internal_marks=rec_in.internal_marks,
                backlogs=rec_in.backlogs,
                semester_cgpa=rec_in.semester_cgpa,
                grade=rec_in.grade,
                historical_risk_level=rec_in.historical_risk_level,
                notes=rec_in.notes
            )
            db.add(record)

        await db.commit()
        await db.refresh(student, ["department", "academic_records"])
        return student

    @staticmethod
    async def get_student_by_id(db: AsyncSession, student_id: uuid.UUID) -> Optional[StudentProfile]:
        stmt = (
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records)
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_students(
        db: AsyncSession,
        search: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        semester: Optional[int] = None,
        is_archived: bool = False,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[StudentProfile], int]:
        query = (
            select(StudentProfile)
            .options(selectinload(StudentProfile.department))
            .where(StudentProfile.is_archived == is_archived)
        )

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    StudentProfile.name.ilike(term),
                    StudentProfile.student_number.ilike(term)
                )
            )

        if department_id:
            query = query.where(StudentProfile.department_id == department_id)

        if semester:
            query = query.where(StudentProfile.current_semester == semester)

        # Count Total
        count_query = select(func.count()).select_from(query.subquery())
        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        # Paginate
        offset = (page - 1) * limit
        query = query.order_by(StudentProfile.student_number.asc()).offset(offset).limit(limit)
        items_res = await db.execute(query)
        items = list(items_res.scalars().all())

        return items, total

    @staticmethod
    async def update_student(
        db: AsyncSession,
        student_id: uuid.UUID,
        student_in: StudentUpdate
    ) -> StudentProfile:
        student = await db.get(StudentProfile, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )

        update_data = student_in.model_dump(exclude_unset=True)

        if "department_id" in update_data and update_data["department_id"]:
            dept = await db.get(Department, update_data["department_id"])
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target department not found"
                )

        for field, value in update_data.items():
            if value is not None:
                if isinstance(value, str):
                    value = value.strip()
                setattr(student, field, value)

        await db.commit()
        await db.refresh(student, ["department"])
        return student

    @staticmethod
    async def archive_student(db: AsyncSession, student_id: uuid.UUID) -> StudentProfile:
        student = await db.get(StudentProfile, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        student.is_archived = True
        await db.commit()
        await db.refresh(student, ["department"])
        return student

    @staticmethod
    async def restore_student(db: AsyncSession, student_id: uuid.UUID) -> StudentProfile:
        student = await db.get(StudentProfile, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        student.is_archived = False
        await db.commit()
        await db.refresh(student, ["department"])
        return student
