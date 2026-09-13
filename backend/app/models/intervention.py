import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Numeric, Integer, Enum, ForeignKey, Uuid, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin


class InterventionStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"


class InterventionCategory(str, enum.Enum):
    ATTENDANCE_SUPPORT = "ATTENDANCE_SUPPORT"
    BACKLOG_SUPPORT = "BACKLOG_SUPPORT"
    EXAM_PREPARATION = "EXAM_PREPARATION"
    SUBJECT_SUPPORT = "SUBJECT_SUPPORT"
    STUDY_PLAN = "STUDY_PLAN"
    ACADEMIC_COUNSELLING = "ACADEMIC_COUNSELLING"
    FACULTY_MEETING = "FACULTY_MEETING"
    PERFORMANCE_REVIEW = "PERFORMANCE_REVIEW"
    OTHER = "OTHER"


class InterventionPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OutcomeStatus(str, enum.Enum):
    IMPROVED = "IMPROVED"
    STABLE = "STABLE"
    DECLINED = "DECLINED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class Intervention(Base, TimestampMixin):
    __tablename__ = "interventions"

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
    faculty_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("faculty_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    category: Mapped[InterventionCategory] = mapped_column(
        Enum(InterventionCategory, native_enum=False, length=50),
        nullable=False,
        default=InterventionCategory.ACADEMIC_COUNSELLING
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    priority: Mapped[InterventionPriority] = mapped_column(
        Enum(InterventionPriority, native_enum=False, length=20),
        nullable=False,
        default=InterventionPriority.MEDIUM
    )
    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, native_enum=False, length=30),
        nullable=False,
        default=InterventionStatus.PLANNED,
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="FACULTY_MANUAL"  # FACULTY_MANUAL, RECOMMENDATION_LINKED, RISK_ALERT
    )
    related_alert_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    related_recommendation_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    follow_up_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Baseline indicators snapshot at creation
    baseline_risk_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    baseline_predicted_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True
    )
    baseline_attendance: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    baseline_backlogs: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        foreign_keys=[student_id]
    )
    faculty: Mapped[Optional["FacultyProfile"]] = relationship(
        "FacultyProfile",
        foreign_keys=[faculty_id]
    )
    outcome: Mapped[Optional["InterventionOutcome"]] = relationship(
        "InterventionOutcome",
        back_populates="intervention",
        uselist=False,
        cascade="all, delete-orphan"
    )


class InterventionOutcome(Base, TimestampMixin):
    __tablename__ = "intervention_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    intervention_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interventions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    previous_risk: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    current_risk: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    previous_predicted_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True
    )
    current_predicted_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True
    )
    previous_attendance: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    current_attendance: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    previous_backlogs: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    current_backlogs: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )
    outcome_status: Mapped[OutcomeStatus] = mapped_column(
        Enum(OutcomeStatus, native_enum=False, length=30),
        nullable=False,
        default=OutcomeStatus.INSUFFICIENT_DATA
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    measured_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    intervention: Mapped["Intervention"] = relationship(
        "Intervention",
        back_populates="outcome"
    )
