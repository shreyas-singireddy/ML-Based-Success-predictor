"""Initial schema creation with users, departments, students, academic records, and prediction baseline

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-13 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Departments
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_departments_code", "departments", ["code"], unique=True)

    # 2. Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, default="STUDENT"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 3. Student Profiles
    op.create_table(
        "student_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True),
        sa.Column("student_number", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("gender", sa.String(20), nullable=False, default="OTHER"),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("enrollment_year", sa.Integer(), nullable=False),
        sa.Column("current_semester", sa.Integer(), nullable=False, default=1),
        sa.Column("cumulative_gpa", sa.Numeric(4, 2), nullable=True),
        sa.Column("total_credits_earned", sa.Integer(), nullable=False, default=0),
        sa.Column("is_archived", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_student_profiles_student_number", "student_profiles", ["student_number"], unique=True)
    op.create_index("ix_student_profiles_department_id", "student_profiles", ["department_id"])
    op.create_index("ix_student_profiles_is_archived", "student_profiles", ["is_archived"])

    # 4. Faculty Profiles
    op.create_table(
        "faculty_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("employee_number", sa.String(50), nullable=False, unique=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_faculty_profiles_employee_number", "faculty_profiles", ["employee_number"], unique=True)

    # 5. Semester Academic Records
    op.create_table(
        "semester_academic_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year", sa.String(9), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("attendance_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("previous_cgpa", sa.Numeric(4, 2), nullable=True),
        sa.Column("mid_1", sa.Numeric(5, 2), nullable=True),
        sa.Column("mid_2", sa.Numeric(5, 2), nullable=True),
        sa.Column("internal_marks", sa.Numeric(5, 2), nullable=True),
        sa.Column("backlogs", sa.Integer(), nullable=False, default=0),
        sa.Column("semester_cgpa", sa.Numeric(4, 2), nullable=True),
        sa.Column("grade", sa.String(10), nullable=True),
        sa.Column("historical_risk_level", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "academic_year", "semester", name="uq_student_academic_term")
    )
    op.create_index("idx_student_semester", "semester_academic_records", ["student_id", "semester"])

    # 6. ML Models Registry Table
    op.create_table(
        "ml_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, unique=True),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("algorithm", sa.String(100), nullable=False),
        sa.Column("evaluation_metrics", sa.JSON(), nullable=True),
        sa.Column("artifact_path", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 7. Predictions Table
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True),
        sa.Column("predicted_cgpa", sa.Numeric(4, 2), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("confidence_category", sa.String(20), nullable=False, default="MODERATE"),
        sa.Column("feature_snapshot", sa.JSON(), nullable=False),
        sa.Column("shap_attributions", sa.JSON(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_predictions_student_id", "predictions", ["student_id"])
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"])

    # 8. Audit Logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("predictions")
    op.drop_table("ml_models")
    op.drop_table("semester_academic_records")
    op.drop_table("faculty_profiles")
    op.drop_table("student_profiles")
    op.drop_table("users")
    op.drop_table("departments")
