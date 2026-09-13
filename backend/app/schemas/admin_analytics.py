"""
Pydantic schemas for Phase 13 System-wide Analytics & Admin Intelligence.
"""

from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class AdminOverviewAnalytics(BaseModel):
    total_students: int
    active_students: int
    students_monitored: int
    average_current_cgpa: Optional[float] = None
    average_predicted_cgpa: Optional[float] = None
    risk_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    )
    risk_percentages: Dict[str, float] = Field(
        default_factory=lambda: {"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.0, "CRITICAL": 0.0}
    )
    students_requiring_attention: int
    total_departments: int
    total_faculty: int
    total_interventions: int
    completed_interventions: int
    follow_ups_due: int
    total_alerts: int


class DepartmentRiskItem(BaseModel):
    department_id: uuid.UUID
    department_name: str
    department_code: str
    student_count: int
    risk_distribution: Dict[str, int]
    high_or_critical_pct: float


class SemesterRiskItem(BaseModel):
    semester: int
    student_count: int
    risk_distribution: Dict[str, int]
    average_cgpa: Optional[float] = None
    average_attendance: Optional[float] = None


class AttendanceVsRiskBucket(BaseModel):
    attendance_bracket: str
    student_count: int
    risk_distribution: Dict[str, int]


class AdminRiskAnalytics(BaseModel):
    risk_distribution: Dict[str, int]
    risk_percentages: Dict[str, float]
    total_high_critical_count: int
    high_critical_percentage: float
    department_risk_breakdown: List[DepartmentRiskItem]
    semester_risk_breakdown: List[SemesterRiskItem]
    attendance_vs_risk: List[AttendanceVsRiskBucket]


class DepartmentPerformanceItem(BaseModel):
    department_id: uuid.UUID
    department_name: str
    department_code: str
    student_count: int
    average_current_cgpa: Optional[float] = None
    average_predicted_cgpa: Optional[float] = None
    average_attendance: Optional[float] = None
    total_backlogs: int
    students_with_backlogs: int
    intervention_count: int


class AdminAcademicPerformanceAnalytics(BaseModel):
    overall_cgpa_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "< 6.0": 0,
            "6.0 - 6.99": 0,
            "7.0 - 7.99": 0,
            "8.0 - 8.99": 0,
            ">= 9.0": 0,
        }
    )
    average_current_cgpa: Optional[float] = None
    average_predicted_cgpa: Optional[float] = None
    average_attendance: Optional[float] = None
    attendance_below_75_count: int = 0
    attendance_below_65_count: int = 0
    total_backlogs: int = 0
    students_with_backlogs_count: int = 0
    students_with_backlogs_pct: float = 0.0
    department_performances: List[DepartmentPerformanceItem] = Field(default_factory=list)


class AdminDepartmentAnalyticsResponse(BaseModel):
    departments: List[DepartmentPerformanceItem]
    total_departments: int


class AdminSemesterAnalyticsResponse(BaseModel):
    semesters: List[SemesterRiskItem]
    total_semesters: int


class AdminInterventionsAnalytics(BaseModel):
    total_interventions: int
    by_status: Dict[str, int]
    by_category: Dict[str, int]
    by_priority: Dict[str, int]
    completion_rate: float
    follow_ups_due_count: int
    outcome_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "IMPROVED": 0,
            "STABLE": 0,
            "DECLINED": 0,
            "INSUFFICIENT_DATA": 0,
        }
    )
    measured_students_count: int
    improved_percentage_of_measured: float
    observational_statement: str = (
        "Evaluation reflects observational changes in academic indicators following intervention records. "
        "No deterministic causal attribution is implied."
    )
