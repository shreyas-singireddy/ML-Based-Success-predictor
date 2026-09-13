"""
Comprehensive test suite for Phase 13: System-wide Analytics & Admin Intelligence.

Tests verify:
1. Authentication & RBAC (Admin required; Students and Faculty rejected with 403, unauthenticated with 401).
2. System Overview Analytics (Total students, active, monitored, CGPA averages, risk counts, interventions).
3. Risk Intelligence Analytics (Risk distribution, percentages, department breakdown, attendance correlation).
4. Academic Performance Analytics (CGPA distribution buckets, backlogs, attendance health).
5. Department Comparative Analytics (Cross-department student counts, CGPAs, attendance).
6. Semester Comparative Analytics (Semesters 1-8 metrics).
7. Intervention Analytics (Status, category, outcome distributions with non-causal statement).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.student import StudentProfile


@pytest.mark.asyncio
async def test_admin_analytics_unauthenticated_returns_401(client: AsyncClient):
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/overview")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_analytics_student_returns_403(client: AsyncClient, student1_token: str):
    headers = {"Authorization": f"Bearer {student1_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/overview", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_analytics_faculty_returns_403(client: AsyncClient, faculty_token: str):
    """Faculty must NOT automatically have access to institution-wide admin analytics."""
    headers = {"Authorization": f"Bearer {faculty_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/overview", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_overview_analytics_success(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_students" in data
    assert data["total_students"] >= 2
    assert "risk_distribution" in data
    assert "risk_percentages" in data
    assert "average_current_cgpa" in data
    assert "total_departments" in data
    assert "total_faculty" in data


@pytest.mark.asyncio
async def test_admin_risk_analytics_success(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/risk", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "risk_distribution" in data
    assert "risk_percentages" in data
    assert "department_risk_breakdown" in data
    assert "semester_risk_breakdown" in data
    assert "attendance_vs_risk" in data


@pytest.mark.asyncio
async def test_admin_performance_analytics_success(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/performance", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "overall_cgpa_distribution" in data
    assert "< 6.0" in data["overall_cgpa_distribution"]
    assert "average_current_cgpa" in data
    assert "average_attendance" in data
    assert "department_performances" in data


@pytest.mark.asyncio
async def test_admin_departments_analytics_success(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/departments", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "departments" in data
    assert data["total_departments"] >= 1


@pytest.mark.asyncio
async def test_admin_semesters_analytics_success(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/semesters", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "semesters" in data
    assert data["total_semesters"] >= 1


@pytest.mark.asyncio
async def test_admin_interventions_analytics_success(
    client: AsyncClient, admin_token: str, db_session: AsyncSession
):
    res_s = await db_session.execute(select(StudentProfile).where(StudentProfile.student_number == "STU-TEST-001"))
    student = res_s.scalar_one()

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create and complete an intervention
    create_res = await client.post(
        f"{settings.API_V1_PREFIX}/interventions",
        json={
            "student_id": str(student.id),
            "category": "SUBJECT_SUPPORT",
            "title": "Mathematics Tutoring",
            "description": "Calculus revision module.",
            "priority": "MEDIUM",
        },
        headers=headers,
    )
    assert create_res.status_code == 201

    res = await client.get(f"{settings.API_V1_PREFIX}/admin/analytics/interventions", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_interventions" in data
    assert data["total_interventions"] >= 1
    assert "by_status" in data
    assert "by_category" in data
    assert "outcome_distribution" in data
    assert "observational_statement" in data
    assert "No deterministic causal attribution" in data["observational_statement"]
