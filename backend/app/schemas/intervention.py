"""
Pydantic schemas for Phase 12 Intervention Tracking & Outcome Management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.intervention import (
    InterventionStatus,
    InterventionCategory,
    InterventionPriority,
    OutcomeStatus,
)


class InterventionBase(BaseModel):
    category: InterventionCategory = InterventionCategory.ACADEMIC_COUNSELLING
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    reason: Optional[str] = Field(None, max_length=500)
    priority: InterventionPriority = InterventionPriority.MEDIUM
    status: InterventionStatus = InterventionStatus.PLANNED
    notes: Optional[str] = None
    source: str = Field("FACULTY_MANUAL", max_length=50)
    related_alert_id: Optional[str] = None
    related_recommendation_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None


class InterventionCreate(InterventionBase):
    student_id: uuid.UUID


class InterventionUpdate(BaseModel):
    category: Optional[InterventionCategory] = None
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=5)
    reason: Optional[str] = Field(None, max_length=500)
    priority: Optional[InterventionPriority] = None
    status: Optional[InterventionStatus] = None
    notes: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None


class InterventionCompleteRequest(BaseModel):
    completion_notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class InterventionFollowUpRequest(BaseModel):
    follow_up_notes: str = Field(..., min_length=3)
    status: Optional[InterventionStatus] = InterventionStatus.COMPLETED
    new_follow_up_date: Optional[datetime] = None


class InterventionOutcomeCreate(BaseModel):
    current_risk: Optional[str] = None
    current_predicted_cgpa: Optional[float] = None
    current_attendance: Optional[float] = None
    current_backlogs: Optional[int] = None
    outcome_status: Optional[OutcomeStatus] = None
    notes: Optional[str] = None


class InterventionOutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    intervention_id: uuid.UUID
    measured_at: datetime
    previous_risk: Optional[str] = None
    current_risk: Optional[str] = None
    previous_predicted_cgpa: Optional[float] = None
    current_predicted_cgpa: Optional[float] = None
    previous_attendance: Optional[float] = None
    current_attendance: Optional[float] = None
    previous_backlogs: Optional[int] = None
    current_backlogs: Optional[int] = None
    outcome_status: OutcomeStatus
    notes: Optional[str] = None
    measured_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class IndicatorDelta(BaseModel):
    indicator: str
    before: Optional[Any] = None
    after: Optional[Any] = None
    delta: Optional[Any] = None
    status: str = Field("INSUFFICIENT_DATA", description="IMPROVED | STABLE | DECLINED | INSUFFICIENT_DATA")


class BeforeAfterComparisonResponse(BaseModel):
    intervention_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    student_number: str
    measured_at: Optional[datetime] = None
    outcome_status: OutcomeStatus = OutcomeStatus.INSUFFICIENT_DATA
    observational_statement: str
    indicators: List[IndicatorDelta] = Field(default_factory=list)
    has_sufficient_data: bool = True
    disclaimer: str = (
        "This evaluation is observational decision support. Indicators reflect measured changes after the "
        "intervention was recorded and do not constitute deterministic causal proof."
    )


class InterventionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    student_name: Optional[str] = None
    student_number: Optional[str] = None
    department_name: Optional[str] = None
    faculty_id: Optional[uuid.UUID] = None
    faculty_name: Optional[str] = None
    category: InterventionCategory
    title: str
    description: str
    reason: Optional[str] = None
    priority: InterventionPriority
    status: InterventionStatus
    notes: Optional[str] = None
    source: str
    related_alert_id: Optional[str] = None
    related_recommendation_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None

    # Baseline indicators snapshot
    baseline_risk_level: Optional[str] = None
    baseline_predicted_cgpa: Optional[float] = None
    baseline_attendance: Optional[float] = None
    baseline_backlogs: Optional[int] = None

    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    outcome: Optional[InterventionOutcomeResponse] = None


class InterventionDetailResponse(InterventionResponse):
    comparison: Optional[BeforeAfterComparisonResponse] = None


class InterventionListResponse(BaseModel):
    items: List[InterventionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class InterventionDashboardStats(BaseModel):
    total_interventions: int = 0
    active_interventions: int = 0
    follow_ups_due: int = 0
    completed_interventions: int = 0
    improved_count: int = 0
    stable_count: int = 0
    declined_count: int = 0
    insufficient_data_count: int = 0
