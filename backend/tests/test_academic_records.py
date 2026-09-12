import pytest
from httpx import AsyncClient
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_add_academic_record_success(client: AsyncClient, faculty_token: str):
    # Get student 1 ID
    res = await client.get(
        f"{settings.API_V1_PREFIX}/students?search=STU-TEST-001",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    student_id = res.json()["items"][0]["id"]

    new_term_record = {
        "academic_year": "2023-2024",
        "semester": 2,
        "attendance_percentage": 88.5,
        "previous_cgpa": 8.50,
        "mid_1": 80.0,
        "mid_2": 84.0,
        "internal_marks": 82.0,
        "backlogs": 0,
        "semester_cgpa": 8.65,
        "grade": "A+",
        "historical_risk_level": "LOW",
        "notes": "Consistent performance"
    }

    add_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/{student_id}/academic-records",
        json=new_term_record,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert add_res.status_code == 201
    data = add_res.json()
    assert data["semester"] == 2
    assert data["academic_year"] == "2023-2024"
    assert data["attendance_percentage"] == 88.5

    # Check that history now has 2 records in chronological order
    hist_res = await client.get(
        f"{settings.API_V1_PREFIX}/students/{student_id}/academic-history",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert hist_res.status_code == 200
    records = hist_res.json()
    assert len(records) == 2
    assert records[0]["semester"] == 1
    assert records[1]["semester"] == 2


@pytest.mark.asyncio
async def test_duplicate_semester_record(client: AsyncClient, faculty_token: str):
    res = await client.get(
        f"{settings.API_V1_PREFIX}/students?search=STU-TEST-001",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    student_id = res.json()["items"][0]["id"]

    # Semester 1 (2023-2024) already exists
    dup_term_record = {
        "academic_year": "2023-2024",
        "semester": 1,
        "attendance_percentage": 90.0
    }

    dup_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/{student_id}/academic-records",
        json=dup_term_record,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_invalid_attendance_and_cgpa_bounds(client: AsyncClient, faculty_token: str):
    res = await client.get(
        f"{settings.API_V1_PREFIX}/students?search=STU-TEST-001",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    student_id = res.json()["items"][0]["id"]

    invalid_record = {
        "academic_year": "2024-2025",
        "semester": 3,
        "attendance_percentage": 105.0,  # Invalid: > 100
        "semester_cgpa": 12.5           # Invalid: > 10
    }

    err_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/{student_id}/academic-records",
        json=invalid_record,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert err_res.status_code == 422
