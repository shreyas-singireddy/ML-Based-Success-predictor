import pytest
from httpx import AsyncClient
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_admin_and_faculty_access(client: AsyncClient, admin_token: str, faculty_token: str):
    # Admin accesses student list
    res_admin = await client.get(
        f"{settings.API_V1_PREFIX}/students",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200

    # Faculty accesses student list
    res_fac = await client.get(
        f"{settings.API_V1_PREFIX}/students",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res_fac.status_code == 200


@pytest.mark.asyncio
async def test_student_rbac_isolation(
    client: AsyncClient,
    admin_token: str,
    student1_token: str,
    student2_token: str
):
    # 1. Get IDs of Student 1 and Student 2
    res = await client.get(
        f"{settings.API_V1_PREFIX}/students",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    items = res.json()["items"]
    stu1 = next(s for s in items if s["student_number"] == "STU-TEST-001")
    stu2 = next(s for s in items if s["student_number"] == "STU-TEST-002")

    # 2. Student 1 is forbidden from general student listing
    res_list = await client.get(
        f"{settings.API_V1_PREFIX}/students",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_list.status_code == 403

    # 3. Student 1 CAN access their own profile
    res_own = await client.get(
        f"{settings.API_V1_PREFIX}/students/{stu1['id']}",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_own.status_code == 200
    assert res_own.json()["student_number"] == "STU-TEST-001"

    # 4. Student 1 CANNOT access Student 2's profile (403 Forbidden)
    res_peer = await client.get(
        f"{settings.API_V1_PREFIX}/students/{stu2['id']}",
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_peer.status_code == 403
    assert "Access denied" in res_peer.json()["error"]["message"]

    # 5. Student 1 cannot create new students
    res_create = await client.post(
        f"{settings.API_V1_PREFIX}/students",
        json={"student_number": "STU-HACK", "name": "Hacker", "gender": "OTHER", "age": 20, "department_id": stu1["department_id"], "enrollment_year": 2024, "current_semester": 1},
        headers={"Authorization": f"Bearer {student1_token}"}
    )
    assert res_create.status_code == 403
