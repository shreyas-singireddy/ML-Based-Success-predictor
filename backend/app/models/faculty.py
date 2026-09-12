import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin


class FacultyProfile(Base, TimestampMixin):
    __tablename__ = "faculty_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    employee_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    designation: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="faculty_profile"
    )
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="faculty_members"
    )
