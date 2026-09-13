"""
Prediction Service for AI CGPA Inference.

Reuses Phase 2 Preprocessor and Phase 3 Best Model artifacts to provide
production inference with dynamic metadata, compatibility verification,
and longitudinal feature construction.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.schemas.prediction import CGPAPredictionRequest, CGPAPredictionResponse, FeatureSummary
from ml.config.pipeline_config import (
    REGISTRY_DIR,
    SCHEMA,
    FEATURE_ACADEMIC_AVG,
    FEATURE_ATTENDANCE_RISK,
    FEATURE_ATTENDANCE_RISK_CAT,
    FEATURE_INTERNAL_AVG,
    FEATURE_MID_TERM_AVG,
    FEATURE_PREV_CGPA_TREND,
    FEATURE_BACKLOG_SEVERITY,
    FEATURE_BACKLOG_SEVERITY_CAT,
    FEATURE_ACADEMIC_STABILITY,
)
from ml.pipelines.engineering import FeatureEngineer

logger = logging.getLogger("student_predictor.prediction_service")


class CGPAPredictionService:
    """Singleton-style service managing artifact loading and CGPA prediction."""

    def __init__(self, registry_dir: Optional[Path] = None):
        # Registry may be overridden at deployment time via MODEL_REGISTRY_PATH.
        from backend.app.core.config import _resolve_registry_path

        self.registry_dir = registry_dir or _resolve_registry_path()
        self._preprocessor = None
        self._model = None
        self._metadata: Dict[str, Any] = {}
        self._feature_engineer = FeatureEngineer()
        self._is_loaded = False

    def load_artifacts(self) -> None:
        """Loads serialized model, preprocessor, and metadata from registry."""
        if self._is_loaded:
            return

        preprocessor_path = self.registry_dir / "preprocessor.joblib"
        model_path = self.registry_dir / "best_model.joblib"
        metadata_path = self.registry_dir / "model_metadata.json"

        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor artifact missing at {preprocessor_path}. Run Phase 2 pipeline.")
        if not model_path.exists():
            raise FileNotFoundError(f"Champion model artifact missing at {model_path}. Run Phase 3 training.")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Model metadata missing at {metadata_path}. Run Phase 3 training.")

        logger.info(f"Loading preprocessor from {preprocessor_path}...")
        self._preprocessor = joblib.load(preprocessor_path)

        logger.info(f"Loading champion model from {model_path}...")
        self._model = joblib.load(model_path)

        with open(metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        # Model Compatibility Check: Assert preprocessor features match model input expectations
        self._verify_artifact_compatibility()

        self._is_loaded = True
        logger.info(f"Loaded CGPA model '{self.model_name}' (version: {self.model_version}).")

    def _verify_artifact_compatibility(self) -> None:
        """Verifies that preprocessor output aligns with the model's feature structure."""
        expected_features = self._metadata.get("feature_names", [])
        if hasattr(self._model, "n_features_in_"):
            model_n_features = self._model.n_features_in_
            if len(expected_features) != model_n_features:
                raise ValueError(
                    f"Model Artifact Compatibility Error: Metadata specifies {len(expected_features)} features, "
                    f"but model expects {model_n_features} features."
                )

    @property
    def model_name(self) -> str:
        return self._metadata.get("model_name", "UnknownModel")

    @property
    def model_version(self) -> str:
        return self._metadata.get("model_version", "unknown_version")

    @property
    def top_feature_contributions(self) -> Dict[str, float]:
        return self._metadata.get("top_feature_importances", {})

    async def prepare_input_dataframe(
        self,
        request: CGPAPredictionRequest,
        db: Optional[AsyncSession] = None,
        current_user: Optional[Any] = None,
    ) -> Tuple[pd.DataFrame, str]:
        """
        Builds a DataFrame from request payload.
        If student_number is provided and DB is available, fetches authorized past historical records
        for accurate longitudinal trend and stability calculations.
        Returns (dataframe, prediction_context).
        """
        prediction_context = "adhoc_student"

        # Base ad-hoc payload
        row_dict = {
            SCHEMA.STUDENT_ID: request.student_number or "adhoc_student",
            SCHEMA.NAME: "Adhoc Student",
            SCHEMA.GENDER: (request.gender or "OTHER").upper(),
            SCHEMA.AGE: request.age or 20,
            SCHEMA.DEPARTMENT: (request.department_code or "CS").upper(),
            SCHEMA.SEMESTER: request.semester or 4,
            SCHEMA.ACADEMIC_YEAR: "2023-2024",
            SCHEMA.ATTENDANCE: request.attendance_percentage,
            SCHEMA.PREVIOUS_CGPA: request.previous_cgpa,
            SCHEMA.MID_1: request.mid_1,
            SCHEMA.MID_2: request.mid_2,
            SCHEMA.INTERNAL_MARKS: request.internal_marks,
            SCHEMA.BACKLOGS: request.backlogs,
        }

        # Check for historical DB records if student_number is given
        if request.student_number and db is not None:
            try:
                from backend.app.models.student import StudentProfile
                from backend.app.models.academic_record import SemesterAcademicRecord

                # RBAC authorization check if current_user is authenticated
                if current_user is not None and hasattr(current_user, "role"):
                    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
                    if user_role == "STUDENT":
                        # Student can only access their own profile
                        stmt_profile = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
                        res_prof = await db.execute(stmt_profile)
                        own_profile = res_prof.scalar_one_or_none()
                        if not own_profile or own_profile.student_number != request.student_number:
                            raise PermissionError("Access Denied: Students can only run predictions for their own academic record.")

                stmt = (
                    select(SemesterAcademicRecord)
                    .join(StudentProfile, SemesterAcademicRecord.student_id == StudentProfile.id)
                    .where(StudentProfile.student_number == request.student_number)
                    .order_by(SemesterAcademicRecord.semester.asc())
                )
                res = await db.execute(stmt)
                records = res.scalars().all()

                if records:
                    # Append historical records strictly prior to current semester (< target semester)
                    history_rows = []
                    target_sem = request.semester or 4
                    for rec in records:
                        if rec.semester < target_sem:
                            history_rows.append({
                                SCHEMA.STUDENT_ID: request.student_number,
                                SCHEMA.NAME: "Student History",
                                SCHEMA.GENDER: (request.gender or "OTHER").upper(),
                                SCHEMA.AGE: request.age or 20,
                                SCHEMA.DEPARTMENT: (request.department_code or "CS").upper(),
                                SCHEMA.SEMESTER: rec.semester,
                                SCHEMA.ACADEMIC_YEAR: rec.academic_year,
                                SCHEMA.ATTENDANCE: float(rec.attendance_percentage or 80.0),
                                SCHEMA.PREVIOUS_CGPA: float(rec.previous_cgpa or request.previous_cgpa),
                                SCHEMA.MID_1: float(rec.mid_1 or 75.0),
                                SCHEMA.MID_2: float(rec.mid_2 or 75.0),
                                SCHEMA.INTERNAL_MARKS: float(rec.internal_marks or 75.0),
                                SCHEMA.BACKLOGS: int(rec.backlogs or 0),
                            })
                    if history_rows:
                        full_df = pd.DataFrame(history_rows + [row_dict])
                        prediction_context = "historical_student"
                        return full_df, prediction_context
            except PermissionError:
                raise
            except Exception as e:
                logger.warning(f"Failed to query historical records for {request.student_number}: {e}")

        return pd.DataFrame([row_dict]), prediction_context

    async def predict_cgpa(
        self,
        request: CGPAPredictionRequest,
        db: Optional[AsyncSession] = None,
        current_user: Optional[Any] = None,
    ) -> CGPAPredictionResponse:
        """Executes the full inference pipeline on a validated request."""
        self.load_artifacts()

        # 1. Prepare raw input DataFrame (with authorized historical records if available)
        raw_df, prediction_context = await self.prepare_input_dataframe(request, db, current_user)

        # 2. Apply Phase 2 Feature Engineering
        featured_df = self._feature_engineer.transform(raw_df)

        # The target row to predict is the last row (current request)
        target_row_idx = len(featured_df) - 1
        current_features = featured_df.iloc[[target_row_idx]].copy()

        # 3. Extract Feature Summary
        summary = FeatureSummary(
            academic_average=float(current_features[FEATURE_ACADEMIC_AVG].iloc[0]),
            attendance_risk_score=float(current_features[FEATURE_ATTENDANCE_RISK].iloc[0]),
            attendance_risk_category=str(current_features[FEATURE_ATTENDANCE_RISK_CAT].iloc[0]),
            internal_average=float(current_features[FEATURE_INTERNAL_AVG].iloc[0]),
            mid_term_average=float(current_features[FEATURE_MID_TERM_AVG].iloc[0]),
            previous_cgpa_trend=float(current_features[FEATURE_PREV_CGPA_TREND].iloc[0]),
            backlog_severity_score=float(current_features[FEATURE_BACKLOG_SEVERITY].iloc[0]),
            backlog_severity_category=str(current_features[FEATURE_BACKLOG_SEVERITY_CAT].iloc[0]),
            academic_stability=float(current_features[FEATURE_ACADEMIC_STABILITY].iloc[0]),
        )

        # 4. Transform via Preprocessor
        transformed_matrix = self._preprocessor.transform(current_features)

        # 5. Predict via Champion Model
        raw_pred = self._model.predict(transformed_matrix)
        pred_value = float(np.clip(raw_pred[0], 0.0, 10.0))
        predicted_cgpa = round(pred_value, 2)

        return CGPAPredictionResponse(
            predicted_cgpa=predicted_cgpa,
            model_name=self.model_name,
            model_version=self.model_version,
            prediction_context=prediction_context,
            feature_summary=summary,
            top_feature_contributions=self.top_feature_contributions,
            status="success",
        )


# Global singleton instance
prediction_service = CGPAPredictionService()
