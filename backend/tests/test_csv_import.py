import pytest
import io
from httpx import AsyncClient
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_csv_upload_validate_and_confirm(client: AsyncClient, admin_token: str):
    csv_content = (
        "student_id,name,gender,age,department,semester,academic_year,attendance,previous_cgpa,mid_1,mid_2,internal_marks,backlogs,semester_cgpa,grade,historical_risk_level\n"
        "STU-CSV-001,John Doe,MALE,20,CS,1,2024-2025,88.5,8.0,80.0,85.0,82.5,0,8.4,A,LOW\n"
        "STU-CSV-002,Jane Smith,FEMALE,21,CS,1,2024-2025,92.0,8.5,90.0,91.0,90.5,0,8.9,A+,LOW\n"
    )

    files = {"file": ("students_valid.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    
    # 1. Preview / Validate
    val_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/import/validate",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["total_rows"] == 2
    assert val_data["valid_rows_count"] == 2
    assert val_data["invalid_rows_count"] == 0
    assert val_data["is_ready_for_import"] is True
    token = val_data["import_batch_token"]

    # 2. Confirm Import
    conf_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/import/confirm",
        json={"import_batch_token": token, "duplicate_policy": "SKIP_EXISTING"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert conf_res.status_code == 200
    conf_data = conf_res.json()
    assert conf_data["created_students"] == 2
    assert conf_data["created_academic_records"] == 2

    # 3. Verify in database listing
    list_res = await client.get(
        f"{settings.API_V1_PREFIX}/students?search=STU-CSV-001",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert list_res.json()["total"] == 1
    assert list_res.json()["items"][0]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_csv_validation_errors(client: AsyncClient, admin_token: str):
    # CSV with invalid attendance (150%), invalid age (12), and invalid department
    csv_content = (
        "student_id,name,gender,age,department,semester,academic_year,attendance\n"
        "STU-ERR-001,Bad Student,MALE,12,INVALID_DEPT,1,2024-2025,150.0\n"
    )

    files = {"file": ("students_err.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    val_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/import/validate",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert val_res.status_code == 200
    data = val_res.json()
    assert data["total_rows"] == 1
    assert data["valid_rows_count"] == 0
    assert data["invalid_rows_count"] == 1
    assert len(data["errors"]) >= 3  # Age, Dept, Attendance errors


@pytest.mark.asyncio
async def test_csv_intra_file_duplicate_detection(client: AsyncClient, admin_token: str):
    # CSV with duplicate student_id in the same term
    csv_content = (
        "student_id,name,gender,age,department,semester,academic_year,attendance\n"
        "STU-DUP-001,First Entry,MALE,20,CS,1,2024-2025,85.0\n"
        "STU-DUP-001,Second Duplicate Entry,MALE,20,CS,1,2024-2025,80.0\n"
    )

    files = {"file": ("students_dup.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    val_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/import/validate",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert val_res.status_code == 200
    data = val_res.json()
    assert data["duplicate_in_file_count"] == 1
    assert data["preview_items"][1]["is_duplicate_in_file"] is True


@pytest.mark.asyncio
async def test_csv_missing_required_headers(client: AsyncClient, admin_token: str):
    # CSV missing department and attendance headers
    csv_content = "student_id,name\nSTU-001,Alice\n"
    files = {"file": ("missing_headers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    
    val_res = await client.post(
        f"{settings.API_V1_PREFIX}/students/import/validate",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert val_res.status_code == 422
    assert "Missing required CSV columns" in val_res.json()["error"]["message"]
