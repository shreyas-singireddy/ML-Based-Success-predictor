import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.student import StudentProfile
from backend.app.models.academic_record import SemesterAcademicRecord
from backend.app.schemas.academic_record import AcademicRecordCreate, AcademicRecordUpdate


class AcademicService:
    @staticmethod
    async def create_academic_record(
        db: AsyncSession,
        student_id: uuid.UUID,
        record_in: AcademicRecordCreate
    ) -> SemesterAcademicRecord:
        student = await db.get(StudentProfile, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )

        # Check term uniqueness
        stmt = (
            select(SemesterAcademicRecord)
            .where(
                SemesterAcademicRecord.student_id == student_id,
                SemesterAcademicRecord.academic_year == record_in.academic_year,
                SemesterAcademicRecord.semester == record_in.semester
            )
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Academic record for semester {record_in.semester} ({record_in.academic_year}) already exists for this student."
            )

        record = SemesterAcademicRecord(
            student_id=student_id,
            academic_year=record_in.academic_year,
            semester=record_in.semester,
            attendance_percentage=record_in.attendance_percentage,
            previous_cgpa=record_in.previous_cgpa,
            mid_1=record_in.mid_1,
            mid_2=record_in.mid_2,
            internal_marks=record_in.internal_marks,
            backlogs=record_in.backlogs,
            semester_cgpa=record_in.semester_cgpa,
            grade=record_in.grade,
            historical_risk_level=record_in.historical_risk_level,
            notes=record_in.notes
        )
        db.add(record)

        # Update student current semester and cumulative GPA if newer
        if record_in.semester >= student.current_semester:
            student.current_semester = record_in.semester
            if record_in.semester_cgpa is not None:
                student.cumulative_gpa = record_in.semester_cgpa

        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_student_academic_history(
        db: AsyncSession,
        student_id: uuid.UUID
    ) -> List[SemesterAcademicRecord]:
        stmt = (
            select(SemesterAcademicRecord)
            .where(SemesterAcademicRecord.student_id == student_id)
            .order_by(SemesterAcademicRecord.semester.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_academic_record(
        db: AsyncSession,
        record_id: uuid.UUID,
        record_in: AcademicRecordUpdate
    ) -> SemesterAcademicRecord:
        record = await db.get(SemesterAcademicRecord, record_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic record not found"
            )

        update_data = record_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(record, field, value)

        await db.commit()
        await db.refresh(record)
        return record
