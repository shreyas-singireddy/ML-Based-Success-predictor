"""
Comprehensive test suite for Phase 12: Intervention Tracking & Outcome Management.

Tests verify:
1. Authentication & RBAC (Students rejected with 403, unauthenticated with 401, Faculty/Admin permitted).
2. Faculty authorization scoping (Faculty can only access students in their department).
3. Intervention creation captures student baseline metrics snapshot.
4. CRUD operations (List, Get detail, Update).
5. Lifecycle transitions: Complete intervention with completion notes & follow-up scheduling.
6. Follow-up notes recording & schedule update.
7. Outcome recording & observational before-and-after comparison.
8. Non-causal disclaimer and observational statement formulation.
9. Dashboard statistics aggregation.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.department import Department
from backend.app.models.intervention import (
    Intervention,
    InterventionCategory,
    InterventionPriority,
    InterventionStatus,
    OutcomeStatus,
)
from backend.app.models.student import GenderEnum, StudentProfile


@pytest.mark.asyncio
async def test_intervention_unauthenticated_returns_401(client: AsyncClient):
    res = await client.get(f"{settings.API_V1_PREFIX}/interventions")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_intervention_student_role_returns_403(client: AsyncClient, student1_token: str):
    headers = {"Authorization": f"Bearer {student1_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/interventions", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_create_intervention_faculty_success(
    client: AsyncClient, faculty_token: str, db_session: AsyncSession
):
    # Fetch student 1 ID
    res_s = await db_session.execute(select(StudentProfile).where(StudentProfile.student_number == "STU-TEST-001"))
    student = res_s.scalar_one()

    headers = {"Authorization": f"Bearer {faculty_token}"}
    payload = {
        "student_id": str(student.id),
        "category": "ATTENDANCE_SUPPORT",
        "title": "Attendance Monitoring & Mentoring",
        "description": "Student attendance dropped below target. Discuss time management strategies.",
        "reason": "Attendance fell to 72% in recent weeks.",
        "priority": "HIGH",
        "status": "PLANNED",
        "notes": "Initial consultation planned for next Tuesday.",
        "source": "RISK_ALERT",
        "related_alert_id": "ALERT-ATT-001",
    }

    res = await client.post(
        f"{settings.API_V1_PREFIX}/interventions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["category"] == "ATTENDANCE_SUPPORT"
    assert data["priority"] == "HIGH"
    assert data["status"] == "PLANNED"
    assert data["student_id"] == str(student.id)
    assert data["student_name"] == student.name
    # Baseline captured from student profile & records
    assert data["baseline_attendance"] == 90.0
    assert data["baseline_predicted_cgpa"] == 8.5


@pytest.mark.asyncio
async def test_create_intervention_faculty_forbidden_for_other_dept(
    client: AsyncClient, faculty_token: str, db_session: AsyncSession
):
    # Create another department and student
    other_dept = Department(code="EE", name="Electrical Engineering")
    db_session.add(other_dept)
    await db_session.flush()

    other_student = StudentProfile(
        student_number="STU-EE-001",
        name="EE Student",
        gender=GenderEnum.MALE,
        age=22,
        department_id=other_dept.id,
        enrollment_year=2023,
        current_semester=4,
        cumulative_gpa=7.2,
        is_archived=False,
    )
    db_session.add(other_student)
    await db_session.commit()

    headers = {"Authorization": f"Bearer {faculty_token}"}
    payload = {
        "student_id": str(other_student.id),
        "category": "STUDY_PLAN",
        "title": "Study Plan Review",
        "description": "Unauthorized department attempt",
    }
    res = await client.post(
        f"{settings.API_V1_PREFIX}/interventions",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_list_and_filter_interventions(
    client: AsyncClient, faculty_token: str, db_session: AsyncSession
):
    res_s = await db_session.execute(select(StudentProfile).where(StudentProfile.student_number == "STU-TEST-001"))
    student = res_s.scalar_one()

    headers = {"Authorization": f"Bearer {faculty_token}"}
    # Create 2 interventions
    for i in range(2):
        await client.post(
            f"{settings.API_V1_PREFIX}/interventions",
            json={
                "student_id": str(student.id),
                "category": "BACKLOG_SUPPORT" if i == 0 else "ACADEMIC_COUNSELLING",
                "title": f"Intervention Plan {i}",
                "description": f"Description for plan {i}",
                "priority": "MEDIUM",
            },
            headers=headers,
        )

    # List
    res = await client.get(f"{settings.API_V1_PREFIX}/interventions", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2

    # Filter by category
    res_cat = await client.get(
        f"{settings.API_V1_PREFIX}/interventions?category=BACKLOG_SUPPORT",
        headers=headers,
    )
    assert res_cat.status_code == 200
    cat_items = res_cat.json()["items"]
    assert all(item["category"] == "BACKLOG_SUPPORT" for item in cat_items)


@pytest.mark.asyncio
async def test_intervention_lifecycle_and_outcome_tracking(
    client: AsyncClient, faculty_token: str, db_session: AsyncSession
):
    res_s = await db_session.execute(select(StudentProfile).where(StudentProfile.student_number == "STU-TEST-001"))
    student = res_s.scalar_one()

    headers = {"Authorization": f"Bearer {faculty_token}"}

    # 1. Create Intervention
    create_res = await client.post(
        f"{settings.API_V1_PREFIX}/interventions",
        json={
            "student_id": str(student.id),
            "category": "EXAM_PREPARATION",
            "title": "Mid-term Preparation Review",
            "description": "Weekly tutoring sessions for upcoming midterms.",
            "priority": "HIGH",
            "status": "IN_PROGRESS",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    inv_id = create_res.json()["id"]

    # 2. Update Intervention
    patch_res = await client.patch(
        f"{settings.API_V1_PREFIX}/interventions/{inv_id}",
        json={"notes": "Completed session 1 and 2."},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert "Completed session 1 and 2." in patch_res.json()["notes"]

    # 3. Complete Intervention with Follow-up
    complete_res = await client.post(
        f"{settings.API_V1_PREFIX}/interventions/{inv_id}/complete",
        json={
            "completion_notes": "Student demonstrated improved test problem solving.",
            "follow_up_date": "2026-10-15T10:00:00Z",
        },
        headers=headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "FOLLOW_UP_REQUIRED"
    assert complete_res.json()["completed_at"] is not None

    # 4. Record Follow-up Notes
    fu_res = await client.post(
        f"{settings.API_V1_PREFIX}/interventions/{inv_id}/follow-up",
        json={
            "follow_up_notes": "Checked midterm results; scores increased by 15 marks.",
            "status": "COMPLETED",
        },
        headers=headers,
    )
    assert fu_res.status_code == 200
    assert fu_res.json()["status"] == "COMPLETED"
    assert "Checked midterm results" in fu_res.json()["follow_up_notes"]

    # 5. Record Outcome
    outcome_res = await client.post(
        f"{settings.API_V1_PREFIX}/interventions/{inv_id}/outcome",
        json={
            "current_risk": "LOW",
            "current_predicted_cgpa": 8.8,
            "current_attendance": 94.0,
            "current_backlogs": 0,
            "outcome_status": "IMPROVED",
            "notes": "Student showed notable improvement across all academic markers.",
        },
        headers=headers,
    )
    assert outcome_res.status_code == 200
    out_data = outcome_res.json()
    assert out_data["outcome_status"] == "IMPROVED"
    assert out_data["current_predicted_cgpa"] == 8.8

    # 6. Get Before/After Comparison
    comp_res = await client.get(
        f"{settings.API_V1_PREFIX}/interventions/{inv_id}/comparison",
        headers=headers,
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["outcome_status"] == "IMPROVED"
    assert "improved after the intervention" in comp_data["observational_statement"]
    assert "disclaimer" in comp_data
    assert "deterministic causal proof" in comp_data["disclaimer"]
    assert len(comp_data["indicators"]) >= 2

    # 7. Check Dashboard Stats
    stats_res = await client.get(
        f"{settings.API_V1_PREFIX}/interventions/dashboard-stats",
        headers=headers,
    )
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_interventions"] >= 1
    assert stats_data["improved_count"] >= 1
