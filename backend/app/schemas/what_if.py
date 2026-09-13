"""
Pydantic Schemas for Phase 7 What-If Academic Simulator.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.prediction import CGPAPredictionRequest


class WhatIfHypotheticalInputs(BaseModel):
    """
    Hypothetical adjustments supplied by the student for simulation.
    All fields are optional for partial overrides; unsupplied fields retain baseline values.
    """
    model_config = ConfigDict(extra="forbid")

    attendance_percentage: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Hypothetical attendance percentage (0.0 - 100.0)",
        json_schema_extra={"example": 85.0}
    )
    mid_1: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Hypothetical Mid-Term 1 score (0.0 - 100.0)",
        json_schema_extra={"example": 80.0}
    )
    mid_2: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Hypothetical Mid-Term 2 score (0.0 - 100.0)",
        json_schema_extra={"example": 82.0}
    )
    internal_marks: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Hypothetical internal assessment marks (0.0 - 100.0)",
        json_schema_extra={"example": 85.0}
    )
    backlogs: Optional[int] = Field(
        None,
        ge=0,
        le=50,
        description="Hypothetical active backlogs count (0 - 50)",
        json_schema_extra={"example": 0}
    )
    previous_cgpa: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Hypothetical prior cumulative GPA (0.0 - 10.0)",
        json_schema_extra={"example": 7.8}
    )


class WhatIfSimulationRequest(BaseModel):
    """
    What-If Simulation request payload.
    Supports authenticated student profile lookup or direct explicit baseline inputs.
    """
    model_config = ConfigDict(extra="forbid")

    student_number: Optional[str] = Field(
        None,
        description="Optional student identifier for database record resolution",
        json_schema_extra={"example": "STU2024001"}
    )
    semester: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Target academic semester (1 - 12)",
        json_schema_extra={"example": 4}
    )
    baseline_inputs: Optional[CGPAPredictionRequest] = Field(
        None,
        description="Optional explicit baseline academic inputs (for ad-hoc or testing)",
    )
    hypothetical_inputs: WhatIfHypotheticalInputs = Field(
        default_factory=WhatIfHypotheticalInputs,
        description="Hypothetical overrides to apply on top of baseline data",
    )


class AcademicState(BaseModel):
    """Academic input indicators snapshot."""
    attendance_percentage: float
    mid_1: float
    mid_2: float
    internal_marks: float
    backlogs: int
    previous_cgpa: float
    semester: int
    department_code: str


class SimulationOutcome(BaseModel):
    """Outcome metrics for baseline or simulated academic scenario."""
    predicted_cgpa: float
    grade: str
    performance_category: str
    risk_level: str
    risk_score: float
    risk_probabilities: Dict[str, float]
    academic_state: AcademicState


class FactorDelta(BaseModel):
    """Detailed differential for a modified academic factor."""
    factor: str
    display_name: str
    baseline_value: float
    simulated_value: float
    delta: float
    unit: str


class SimulationDelta(BaseModel):
    """Comparative differential between baseline and simulated states."""
    cgpa_delta: float
    cgpa_trend: str  # "IMPROVED", "UNCHANGED", "WORSENED"
    risk_score_delta: float
    risk_transition: str  # e.g. "MEDIUM -> LOW"
    risk_trend: str  # "IMPROVED", "UNCHANGED", "WORSENED"
    performance_category_transition: str  # e.g. "AVERAGE -> GOOD"
    modified_factors: List[FactorDelta]
    overall_impact: str  # "IMPROVED", "UNCHANGED", "WORSENED"


class WhatIfSimulationResponse(BaseModel):
    """Complete What-If Simulation Response."""
    baseline: SimulationOutcome
    simulation: SimulationOutcome
    delta: SimulationDelta
    model_name: str
    model_version: str
    risk_model_name: str
    risk_model_version: str
    status: str = "success"
    disclaimer: str = (
        "Simulations are hypothetical model estimations based on machine learning inference. "
        "They do not alter official academic records or guarantee future examination outcomes."
    )
