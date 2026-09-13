import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, Enum, JSON, DateTime, Uuid, Index, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin


class AlertType(str, enum.Enum):
    RISK_INCREASED = "RISK_INCREASED"
    RISK_CRITICAL = "RISK_CRITICAL"
    PREDICTED_CGPA_DECLINED = "PREDICTED_CGPA_DECLINED"
    ATTENDANCE_LOW = "ATTENDANCE_LOW"
    ATTENDANCE_DECLINED = "ATTENDANCE_DECLINED"
    NEW_BACKLOG = "NEW_BACKLOG"
    BACKLOG_INCREASED = "BACKLOG_INCREASED"
    ASSESSMENT_DECLINED = "ASSESSMENT_DECLINED"
    ACADEMIC_TREND_DECLINING = "ACADEMIC_TREND_DECLINING"
    RISK_SCORE_INCREASED = "RISK_SCORE_INCREASED"
    RISK_DECREASED = "RISK_DECREASED"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    SMS = "SMS"


class MonitoringRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class AcademicSnapshot(Base, TimestampMixin):
    __tablename__ = "academic_snapshots"

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
    monitoring_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    academic_year: Mapped[str] = mapped_column(
        String(9),
        nullable=False
    )
    current_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True
    )
    predicted_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    risk_score: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2),
        nullable=True
    )
    attendance_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    backlogs: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    mid_1: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    mid_2: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    internal_marks: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )
    feature_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    prediction_model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    risk_model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="continuous_monitoring"
    )

    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="academic_snapshots"
    )
    monitoring_run: Mapped[Optional["MonitoringRun"]] = relationship(
        "MonitoringRun",
        back_populates="snapshots"
    )

    __table_args__ = (
        Index("ix_academic_snapshots_student_created", "student_id", "created_at"),
        Index("ix_academic_snapshots_student_semester", "student_id", "semester"),
    )


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

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
    monitoring_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitoring_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, native_enum=False, length=50),
        nullable=False,
        index=True
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, native_enum=False, length=20),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, native_enum=False, length=20),
        nullable=False,
        default=AlertStatus.UNREAD,
        index=True
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="continuous_monitoring"
    )
    prediction_model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    risk_model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolution_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    cooldown_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )

    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="alerts"
    )
    monitoring_run: Mapped[Optional["MonitoringRun"]] = relationship(
        "MonitoringRun",
        back_populates="alerts"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="alert",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_alerts_student_status", "student_id", "status"),
        Index("ix_alerts_student_type_status", "student_id", "alert_type", "status"),
        UniqueConstraint("student_id", "alert_type", "status", "cooldown_until", name="uq_alert_dedup_cooldown"),
    )


class MonitoringRun(Base, TimestampMixin):
    __tablename__ = "monitoring_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    status: Mapped[MonitoringRunStatus] = mapped_column(
        Enum(MonitoringRunStatus, native_enum=False, length=20),
        nullable=False,
        default=MonitoringRunStatus.PENDING,
        index=True
    )
    students_checked: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    signals_detected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    alerts_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    notifications_sent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    errors_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    triggered_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="scheduled"
    )
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    configuration_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    snapshots: Mapped[List["AcademicSnapshot"]] = relationship(
        "AcademicSnapshot",
        back_populates="monitoring_run",
        cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="monitoring_run",
        cascade="all, delete-orphan"
    )


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, native_enum=False, length=20),
        nullable=False,
        default=NotificationChannel.IN_APP
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    failed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    alert: Mapped["Alert"] = relationship(
        "Alert",
        back_populates="notifications"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications"
    )

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read_at"),
        Index("ix_notifications_user_channel", "user_id", "channel"),
    )


# Need to add back_populates to existing models
# This will be handled by updating the existing model files


# Type hints for forward references
from backend.app.models.student import StudentProfile
from backend.app.models.user import User