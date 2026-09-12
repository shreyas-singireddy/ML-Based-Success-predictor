"""
AI Academic Risk Inference Service for Phase 4.

Orchestrates:
1. Phase 3 CGPA Prediction Engine integration (Predicted CGPA, Grade, Performance Category).
2. Phase 2 Preprocessing & Feature Engineering reuse.
3. Phase 4 Champion Risk Classifier execution (LOW, MEDIUM, HIGH, CRITICAL).
4. Probability-weighted continuous normalized risk score calculation ([0.0, 100.0]).
5. Transparent 5-factor deterministic policy breakdown.
6. RBAC authorization and temporal historical context lookup.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.prediction import CGPAPredictionRequest
from backend.app.schemas.risk_prediction import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    RiskFactorDetail,
)
from backend.app.services.prediction_service import prediction_service
from ml.config.pipeline_config import REGISTRY_DIR, SCHEMA
from ml.classification.risk_policy import (
    RISK_CLASSES,
    RiskPolicyEngine,
    calculate_normalized_risk_score,
    map_cgpa_to_grade,
    map_cgpa_to_performance_category,
)
from ml.classification.risk_models import extract_aligned_probabilities

logger = logging.getLogger("student_predictor.risk_service")


class AcademicRiskService:
    """Singleton service managing AI Academic Risk prediction and factor analysis."""

    def __init__(self, registry_dir: Optional[Path] = None):
        self.registry_dir = registry_dir or REGISTRY_DIR
        self._preprocessor = None
        self._model = None
        self._metadata: Dict[str, Any] = {}
        self._is_loaded = False

    def load_artifacts(self) -> None:
        """Loads serialized risk classifier, preprocessor, and metadata from registry."""
        if self._is_loaded:
            return

        preprocessor_path = self.registry_dir / "preprocessor.joblib"
        model_path = self.registry_dir / "best_risk_classifier.joblib"
        metadata_path = self.registry_dir / "risk_metadata.json"

        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor artifact missing at {preprocessor_path}. Run Phase 2 pipeline.")
        if not model_path.exists():
            raise FileNotFoundError(f"Champion risk classifier artifact missing at {model_path}. Run Phase 4 training.")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Risk model metadata missing at {metadata_path}. Run Phase 4 training.")

        logger.info(f"Loading preprocessor from {preprocessor_path}...")
        self._preprocessor = joblib.load(preprocessor_path)

        logger.info(f"Loading champion risk classifier from {model_path}...")
        self._model = joblib.load(model_path)

        with open(metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        self._verify_artifact_compatibility()
        self._is_loaded = True
        logger.info(f"Loaded Academic Risk model '{self.model_name}' (version: {self.model_version}).")

    def _verify_artifact_compatibility(self) -> None:
        """Verifies that preprocessor output aligns with the model's feature structure."""
        expected_features = self._metadata.get("feature_names", [])
        raw_m = self._model.model if hasattr(self._model, "model") else self._model
        if hasattr(raw_m, "n_features_in_"):
            model_n_features = raw_m.n_features_in_
            if expected_features and len(expected_features) != model_n_features:
                raise ValueError(
                    f"Risk Model Artifact Compatibility Error: Metadata specifies {len(expected_features)} features, "
                    f"but model expects {model_n_features} features."
                )

    @property
    def model_name(self) -> str:
        return self._metadata.get("model_name", "DecisionTreeClassifier")

    @property
    def model_version(self) -> str:
        return self._metadata.get("model_version", "risk_v1.0.0")

    @property
    def class_order(self) -> list:
        return self._metadata.get("class_order", RISK_CLASSES)

    async def predict_risk(
        self,
        request: RiskPredictionRequest,
        db: Optional[AsyncSession] = None,
        current_user: Optional[Any] = None,
    ) -> RiskPredictionResponse:
        """Executes full academic risk prediction and multi-indicator factor breakdown."""
        self.load_artifacts()

        # 1. Reuse Phase 3 CGPA Prediction Engine for projected CGPA and context
        cgpa_request = CGPAPredictionRequest(
            student_number=request.student_number,
            gender=request.gender,
            age=request.age,
            department_code=request.department_code,
            semester=request.semester,
            attendance_percentage=request.attendance_percentage,
            previous_cgpa=request.previous_cgpa,
            mid_1=request.mid_1,
            mid_2=request.mid_2,
            internal_marks=request.internal_marks,
            backlogs=request.backlogs,
        )

        cgpa_response = await prediction_service.predict_cgpa(cgpa_request, db, current_user)
        predicted_cgpa = cgpa_response.predicted_cgpa
        prediction_context = cgpa_response.prediction_context
        feature_summary = cgpa_response.feature_summary

        # 2. Derive Institutional Performance Category and Grade from predicted CGPA
        performance_category = map_cgpa_to_performance_category(predicted_cgpa)
        grade = map_cgpa_to_grade(predicted_cgpa)

        # 3. Prepare input DataFrame through Phase 2 Feature Engineering
        raw_df, _ = await prediction_service.prepare_input_dataframe(cgpa_request, db, current_user)
        featured_df = prediction_service._feature_engineer.transform(raw_df)
        current_features = featured_df.iloc[[-1]].copy()

        # 4. Transform features via Phase 2 Preprocessor
        transformed_matrix = self._preprocessor.transform(current_features)

        # 5. Predict Risk Class and Aligned Probabilities
        raw_preds = self._model.predict(transformed_matrix)
        risk_level = str(raw_preds[0])

        aligned_probs_arr = extract_aligned_probabilities(self._model, transformed_matrix, RISK_CLASSES)
        risk_probabilities = {
            cls_name: round(float(aligned_probs_arr[0, idx]), 4)
            for idx, cls_name in enumerate(RISK_CLASSES)
        }

        # 6. Calculate continuous normalized risk score
        risk_score = calculate_normalized_risk_score(risk_probabilities)

        # 7. Generate deterministic 5-factor policy breakdown
        mid_terms_avg = (request.mid_1 + request.mid_2) / 2.0
        trend_val = feature_summary.previous_cgpa_trend if feature_summary else 0.0

        factors_raw = RiskPolicyEngine.generate_risk_factor_breakdown(
            attendance=request.attendance_percentage,
            backlogs=request.backlogs,
            mid_terms=mid_terms_avg,
            previous_cgpa=request.previous_cgpa,
            academic_trend=trend_val,
        )
        risk_factors = [RiskFactorDetail(**f) for f in factors_raw]

        return RiskPredictionResponse(
            predicted_cgpa=predicted_cgpa,
            grade=grade,
            performance_category=performance_category,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_probabilities=risk_probabilities,
            risk_factors=risk_factors,
            model_name=self.model_name,
            model_version=self.model_version,
            prediction_context=prediction_context,
            status="success",
        )


# Global singleton instance
academic_risk_service = AcademicRiskService()
