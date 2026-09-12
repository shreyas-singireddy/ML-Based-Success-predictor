import pytest
from httpx import AsyncClient
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_list_students(client: AsyncClient, admin_token: str):
    res = await client.get(
        f"{settings.API_V1_PREFIX}/students",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_create_student_success(client: AsyncClient, admin_token: str, db_session):
    # First get department ID
    dept_res = await client.get(
        f"{settings.API_V1_PREFIX}/departments",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    dept_id = dept_res.json()[0]["id"]

    new_student = {
        "student_number": "STU-TEST-003",
        "name": "Emily Blunt",
        "gender": "FEMALE",
        "age": 22,
        "department_id": dept_id,
        "enrollment_year": 2024,
        "current_semester": 1,
        "cumulative_gpa": 8.0,
        "total_credits_earned": 20,
        "initial_academic_record": {
            "academic_year": "2024-2025",
            "semester": 1,
            "attendance_percentage": 91.0,
            "mid_1": 85.0,
            "mid_2": 88.0,
            "internal_marks": 86.5,
            "backlogs": 0,
            "semester_cgpa": 8.0,
            "grade": "A"
        }
    }

    res = await client.post(
        f"{settings.API_V1_PREFIX}/students",
        json=new_student,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["student_number"] == "STU-TEST-003"
    assert data["name"] == "Emily Blunt"
    assert len(data["academic_records"]) == 1
    assert data["academic_records"][0]["attendance_percentage"] == 91.0


@pytest.mark.asyncio
async def test_create_duplicate_student_number(client: AsyncClient, admin_token: str):
    dept_res = await client.get(
        f"{settings.API_V1_PREFIX}/departments",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    dept_id = dept_res.json()[0]["id"]

    dup_student = {
        "student_number": "STU-TEST-001",  # Already exists in fixture
        "name": "Duplicate Student",
        "gender": "MALE",
        "age": 20,
        "department_id": dept_id,
        "enrollment_year": 2023,
        "current_semester": 1
    }

    res = await client.post(
        f"{settings.API_V1_PREFIX}/students",
        json=dup_student,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 409
    assert "already exists" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_search_and_filter_students(client: AsyncClient, admin_token: str):
    # Search by student number
    res = await client.get(
        f"{settings.API_V1_PREFIX}/students?search=STU-TEST-001",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["student_number"] == "STU-TEST-001"

    # Search by non-existent name
    res_empty = await client.get(
        f"{settings.API_V1_PREFIX}/students?search=NonExistentPerson",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_empty.status_code == 200
    assert res_empty.json()["total"] == 0


@pytest.mark.asyncio
async def test_archive_and_restore_student(client: AsyncClient, admin_token: str):
    # Get student 1 ID
    res = await client.get(
        f"{settings.API_V1_PREFIX}/students?search=STU-TEST-001",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    student_id = res.json()["items"][0]["id"]

    # Archive (Soft Delete)
    del_res = await client.delete(
        f"{settings.API_V1_PREFIX}/students/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 200
    assert del_res.json()["is_archived"] is True

    # Check that student is omitted from active listing
    active_res = await client.get(
        f"{settings.API_V1_PREFIX}/students?is_archived=false",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert active_res.json()["total"] == 1

    # Check that student appears in archived listing
    archived_res = await client.get(
        f"{settings.API_V1_PREFIX}/students?is_archived=true",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert archived_res.json()["total"] == 1
    assert archived_res.json()["items"][0]["student_number"] == "STU-TEST-001"

    # Restore student
    restore_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/{student_id}/restore",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert restore_res.status_code == 200
    assert restore_res.json()["is_archived"] is False
