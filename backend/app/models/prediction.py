import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Boolean, ForeignKey, JSON, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    version: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )
    model_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    algorithm: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    evaluation_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    artifact_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class Prediction(Base):
    __tablename__ = "predictions"

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
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ml_models.id", ondelete="SET NULL"),
        nullable=True
    )
    predicted_cgpa: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        comment="Model-generated predicted continuous CGPA"
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Model-generated risk category (LOW, MODERATE, HIGH, CRITICAL)"
    )
    confidence_score: Mapped[float] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        comment="Calibrated output probability (0.000 to 1.000)"
    )
    confidence_category: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MODERATE"
    )
    feature_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Snapshot of input feature vector used during inference"
    )
    shap_attributions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="TreeSHAP local feature importance explanations"
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
