import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Integer, Numeric, Boolean, Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin


class GenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    NON_BINARY = "NON_BINARY"


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True
    )
    student_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )
    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum, native_enum=False, length=20),
        nullable=False,
        default=GenderEnum.OTHER
    )
    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    enrollment_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    current_semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    cumulative_gpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True
    )
    total_credits_earned: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="student_profile"
    )
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="students"
    )
    academic_records: Mapped[List["SemesterAcademicRecord"]] = relationship(
        "SemesterAcademicRecord",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="SemesterAcademicRecord.semester"
    )
    academic_snapshots: Mapped[List["AcademicSnapshot"]] = relationship(
        "AcademicSnapshot",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="AcademicSnapshot.created_at.desc()"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="Alert.created_at.desc()"
    )
