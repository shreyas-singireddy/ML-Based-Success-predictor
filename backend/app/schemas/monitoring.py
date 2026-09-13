"""
Pydantic schemas for Phase 11: Continuous Academic Monitoring & Early-Warning Alert Engine.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.monitoring import (
    AlertType,
    AlertSeverity,
    AlertStatus,
    NotificationChannel,
    MonitoringRunStatus,
)


class AcademicSnapshotBase(BaseModel):
    semester: int = Field(..., ge=1, le=12)
    academic_year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
    current_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    predicted_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    risk_level: Optional[str] = Field(None, max_length=20)
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    attendance_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    backlogs: int = Field(0, ge=0)
    mid_1: Optional[float] = Field(None, ge=0.0, le=100.0)
    mid_2: Optional[float] = Field(None, ge=0.0, le=100.0)
    internal_marks: Optional[float] = Field(None, ge=0.0, le=100.0)
    feature_snapshot: Optional[Dict[str, Any]] = None
    prediction_model_version: Optional[str] = None
    risk_model_version: Optional[str] = None
    source: str = Field("continuous_monitoring", max_length=50)


class AcademicSnapshotCreate(AcademicSnapshotBase):
    student_id: uuid.UUID
    monitoring_run_id: Optional[uuid.UUID] = None


class AcademicSnapshotResponse(AcademicSnapshotBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    monitoring_run_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class AlertEvidence(BaseModel):
    """Structured evidence for why an alert was generated."""
    previous_value: Optional[Any] = None
    current_value: Optional[Any] = None
    threshold: Optional[Any] = None
    change_magnitude: Optional[float] = None
    change_direction: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None


class AlertBase(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=5)
    evidence: AlertEvidence
    source: str = Field("continuous_monitoring", max_length=50)
    prediction_model_version: Optional[str] = None
    risk_model_version: Optional[str] = None


class AlertCreate(AlertBase):
    student_id: uuid.UUID
    monitoring_run_id: Optional[uuid.UUID] = None


class AlertUpdate(BaseModel):
    status: Optional[AlertStatus] = None
    acknowledged_by: Optional[uuid.UUID] = None
    resolution_reason: Optional[str] = None


class AlertResponse(AlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    monitoring_run_id: Optional[uuid.UUID] = None
    status: AlertStatus
    acknowledged_by: Optional[uuid.UUID] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_reason: Optional[str] = None
    cooldown_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Related data
    student_number: Optional[str] = None
    student_name: Optional[str] = None


class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: uuid.UUID


class AlertResolveRequest(BaseModel):
    resolution_reason: str = Field(..., min_length=3)


class MonitoringRunBase(BaseModel):
    triggered_by: str = Field("scheduled", max_length=50)
    triggered_by_user_id: Optional[uuid.UUID] = None
    configuration_snapshot: Optional[Dict[str, Any]] = None


class MonitoringRunCreate(MonitoringRunBase):
    pass


class MonitoringRunResponse(MonitoringRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: MonitoringRunStatus
    students_checked: int
    signals_detected: int
    alerts_created: int
    notifications_sent: int
    errors_count: int
    error_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class MonitoringRunListResponse(BaseModel):
    items: List[MonitoringRunResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class MonitoringRunStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    status: MonitoringRunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    students_checked: int
    signals_detected: int
    alerts_created: int
    notifications_sent: int
    errors_count: int
    error_details: Optional[Dict[str, Any]] = None


class NotificationBase(BaseModel):
    channel: NotificationChannel = NotificationChannel.IN_APP
    title: str = Field(..., min_length=3, max_length=200)
    body: str = Field(..., min_length=5)
    external_id: Optional[str] = None


class NotificationCreate(NotificationBase):
    alert_id: uuid.UUID
    user_id: uuid.UUID


class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    alert_id: uuid.UUID
    user_id: uuid.UUID
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed: bool
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class UnreadCountResponse(BaseModel):
    unread_count: int
    by_severity: Dict[str, int]


class MonitoringConfiguration(BaseModel):
    """Configuration for monitoring thresholds and policies."""
    attendance_alert_threshold: float = Field(75.0, ge=0.0, le=100.0)
    attendance_critical_threshold: float = Field(65.0, ge=0.0, le=100.0)
    attendance_decline_threshold: float = Field(10.0, ge=0.0, le=100.0)
    risk_score_change_threshold: float = Field(15.0, ge=0.0, le=100.0)
    predicted_cgpa_change_threshold: float = Field(0.3, ge=0.0, le=10.0)
    assessment_drop_threshold: float = Field(15.0, ge=0.0, le=100.0)
    trend_min_data_points: int = Field(3, ge=2, le=10)
    alert_cooldown_hours: int = Field(24, ge=1, le=168)
    monitoring_interval_minutes: int = Field(60, ge=5, le=1440)
    batch_size: int = Field(100, ge=10, le=500)


class SignalDetectionResult(BaseModel):
    """Result of a single signal detection check."""
    alert_type: AlertType
    detected: bool
    severity: Optional[AlertSeverity] = None
    evidence: AlertEvidence
    title: str = ""
    message: str = ""


class StudentMonitoringResult(BaseModel):
    """Result of monitoring a single student."""
    student_id: uuid.UUID
    student_number: str
    student_name: str
    signals: List[SignalDetectionResult]
    alerts_created: int
    errors: List[str]


class MonitoringSummary(BaseModel):
    """Summary of a monitoring run."""
    run_id: uuid.UUID
    students_processed: int
    total_signals: int
    alerts_by_type: Dict[str, int]
    alerts_by_severity: Dict[str, int]
    notifications_sent: int
    duration_seconds: float


class ChangeDetectionInput(BaseModel):
    """Input data for change detection."""
    student_id: uuid.UUID
    student_number: str
    current_snapshot: AcademicSnapshotBase
    previous_snapshot: Optional[AcademicSnapshotBase] = None
    academic_records: List[Dict[str, Any]] = Field(default_factory=list)


# Frontend-specific schemas for notification center
class NotificationCenterItem(BaseModel):
    """Simplified alert for notification center display."""
    id: uuid.UUID
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    created_at: datetime
    status: AlertStatus
    student_number: Optional[str] = None
    student_name: Optional[str] = None


class StudentNotificationCenterResponse(BaseModel):
    """Response for student notification center."""
    notifications: List[NotificationCenterItem]
    unread_count: int
    unread_by_severity: Dict[str, int]


class FacultyNotificationCenterResponse(BaseModel):
    """Response for faculty notification center."""
    notifications: List[NotificationCenterItem]
    unread_count: int
    unread_by_severity: Dict[str, int]
    critical_students: List[str]


class AlertDetailResponse(BaseModel):
    """Detailed alert view."""
    alert: AlertResponse
    related_student_summary: Optional[Dict[str, Any]] = None
    can_acknowledge: bool = False
    can_resolve: bool = False