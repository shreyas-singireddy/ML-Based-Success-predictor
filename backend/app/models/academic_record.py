import uuid
from typing import Optional
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, UniqueConstraint, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin


class SemesterAcademicRecord(Base, TimestampMixin):
    __tablename__ = "semester_academic_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    academic_year: Mapped[str] = mapped_column(
        String(9),
        nullable=False,
        comment="Academic year formatted strictly as YYYY-YYYY (e.g. 2024-2025)"
    )
    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Semester index (1 to 12)"
    )
    attendance_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Attendance percentage between 0.00 and 100.00"
    )
    previous_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="Previous cumulative GPA prior to this semester"
    )
    mid_1: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Mid-term exam 1 marks (0.00 to 100.00)"
    )
    mid_2: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Mid-term exam 2 marks (0.00 to 100.00)"
    )
    internal_marks: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Continuous assessment / internal marks (0.00 to 100.00)"
    )
    backlogs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Non-negative count of pending failed courses"
    )
    semester_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="Actual official recorded term CGPA/SGPA (0.00 to 10.00)"
    )
    grade: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Official recorded letter grade (e.g. O, A+, A, B, F)"
    )
    historical_risk_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Temporary Phase-1 legacy compatibility field for imported/manual risk. Dynamic ML risk is stored in 'predictions'."
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="academic_records"
    )

    __table_args__ = (
        UniqueConstraint("student_id", "academic_year", "semester", name="uq_student_academic_term"),
        Index("idx_student_semester", "student_id", "semester"),
    )
