import io
import re
import csv
import uuid
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.models.department import Department
from backend.app.models.student import StudentProfile, GenderEnum
from backend.app.models.academic_record import SemesterAcademicRecord
from backend.app.schemas.csv_import import (
    ImportDuplicatePolicy,
    CSVValidationPreview,
    CSVPreviewItem,
    CSVRowError,
    CSVImportResult
)

# In-memory session store for validated preview batches (with batch_id -> data)
_PREVIEW_STORE: Dict[str, Dict[str, Any]] = {}


def sanitize_csv_text(val: Any) -> str:
    """Strip formula injection triggers (=, +, -, @) and excess whitespace."""
    if val is None:
        return ""
    text = str(val).strip()
    if text.startswith(("=", "+", "-", "@")):
        text = text[1:].strip()
    return text


class CSVService:
    # Header aliases for forgiving parsing
    HEADER_MAPPINGS = {
        "student_id": ["student_id", "student_number", "roll_no", "id", "studentid", "studentno"],
        "name": ["name", "student_name", "fullname", "full_name"],
        "gender": ["gender", "sex"],
        "age": ["age"],
        "department": ["department", "dept", "department_code", "branch"],
        "semester": ["semester", "sem", "current_semester"],
        "academic_year": ["academic_year", "acad_year", "year", "session"],
        "attendance": ["attendance", "attendance_percentage", "attendance_%", "attendance_pct"],
        "previous_cgpa": ["previous_cgpa", "prev_cgpa", "prior_cgpa", "last_cgpa"],
        "mid_1": ["mid_1", "mid1", "mid_term_1", "midterm1"],
        "mid_2": ["mid_2", "mid2", "mid_term_2", "midterm2"],
        "internal_marks": ["internal_marks", "internals", "internal", "internal_score"],
        "backlogs": ["backlogs", "backlog_count", "arrears", "failed_subjects"],
        "semester_cgpa": ["semester_cgpa", "sem_cgpa", "cgpa", "sgpa", "gpa"],
        "grade": ["grade", "letter_grade", "final_grade"],
        "historical_risk_level": ["historical_risk_level", "risk_level", "risk", "legacy_risk"]
    }

    @classmethod
    def _normalize_headers(cls, raw_headers: List[str]) -> Dict[str, int]:
        normalized_map: Dict[str, int] = {}
        for idx, header in enumerate(raw_headers):
            clean = header.strip().lower().replace(" ", "_")
            for canonical, aliases in cls.HEADER_MAPPINGS.items():
                if clean in aliases and canonical not in normalized_map:
                    normalized_map[canonical] = idx
                    break
        return normalized_map

    @classmethod
    async def parse_and_preview_csv(
        cls,
        db: AsyncSession,
        file: UploadFile
    ) -> CSVValidationPreview:
        # 1. File validation
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv files are supported")

        content = await file.read()
        max_bytes = settings.MAX_CSV_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_CSV_UPLOAD_SIZE_MB}MB"
            )

        try:
            text_content = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text_content = content.decode("latin-1")
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to decode CSV file encoding")

        # 2. Parse CSV rows
        reader = csv.reader(io.StringIO(text_content))
        rows = list(reader)
        if not rows:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty")

        header_row = rows[0]
        header_map = cls._normalize_headers(header_row)

        # Check critical required columns
        required_cols = ["student_id", "name", "department", "semester", "attendance"]
        missing_cols = [col for col in required_cols if col not in header_map]
        if missing_cols:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required CSV columns: {', '.join(missing_cols)}"
            )

        # 3. Preload all departments for fast lookup
        dept_stmt = select(Department)
        dept_res = await db.execute(dept_stmt)
        all_depts = list(dept_res.scalars().all())
        dept_lookup = {d.code.upper(): d for d in all_depts}
        dept_name_lookup = {d.name.lower(): d for d in all_depts}

        # 4. Preload existing student numbers & records from DB
        student_stmt = select(StudentProfile).options(selectinload(StudentProfile.academic_records))
        student_res = await db.execute(student_stmt)
        existing_students = {s.student_number: s for s in student_res.scalars().all()}

        # 5. Row-by-row validation
        preview_items: List[CSVPreviewItem] = []
        all_errors: List[CSVRowError] = []
        seen_file_keys: Dict[Tuple[str, str, int], int] = {}  # (student_id, acad_year, sem) -> first_row

        current_year = datetime.now(timezone.utc).year
        default_academic_year = f"{current_year}-{current_year + 1}"

        for row_idx, row in enumerate(rows[1:], start=2):
            if not row or all(not cell.strip() for cell in row):
                continue  # Skip empty line

            def get_val(col_name: str) -> str:
                if col_name in header_map and header_map[col_name] < len(row):
                    return sanitize_csv_text(row[header_map[col_name]])
                return ""

            raw_student_id = get_val("student_id")
            raw_name = get_val("name")
            raw_gender = get_val("gender").upper() or "OTHER"
            raw_age = get_val("age")
            raw_dept = get_val("department").upper()
            raw_sem = get_val("semester")
            raw_acad_year = get_val("academic_year") or default_academic_year
            raw_attendance = get_val("attendance")
            raw_prev_cgpa = get_val("previous_cgpa")
            raw_mid1 = get_val("mid_1")
            raw_mid2 = get_val("mid_2")
            raw_internal = get_val("internal_marks")
            raw_backlogs = get_val("backlogs") or "0"
            raw_sem_cgpa = get_val("semester_cgpa")
            raw_grade = get_val("grade")
            raw_risk = get_val("historical_risk_level")

            row_errors: List[str] = []

            # Validation: student_id
            if not raw_student_id:
                row_errors.append("Student ID is required")
                all_errors.append(CSVRowError(row_number=row_idx, field="student_id", error_message="Student ID is required"))

            # Validation: name
            if not raw_name:
                row_errors.append("Name is required")
                all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="name", error_message="Name is required"))

            # Validation: gender
            parsed_gender = GenderEnum.OTHER
            if raw_gender:
                if raw_gender in [g.value for g in GenderEnum]:
                    parsed_gender = GenderEnum(raw_gender)
                elif raw_gender in ["M", "MALE"]:
                    parsed_gender = GenderEnum.MALE
                elif raw_gender in ["F", "FEMALE"]:
                    parsed_gender = GenderEnum.FEMALE
                else:
                    parsed_gender = GenderEnum.OTHER

            # Validation: age
            parsed_age: Optional[int] = 20
            if raw_age:
                try:
                    parsed_age = int(raw_age)
                    if parsed_age < 15 or parsed_age > 100:
                        row_errors.append("Age must be between 15 and 100")
                        all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="age", error_message="Age must be 15-100", raw_value=raw_age))
                except ValueError:
                    row_errors.append("Age must be a valid integer")
                    all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="age", error_message="Age is not an integer", raw_value=raw_age))

            # Validation: department
            matched_dept = dept_lookup.get(raw_dept) or dept_name_lookup.get(raw_dept.lower())
            if not matched_dept:
                available_codes = ", ".join(dept_lookup.keys())
                row_errors.append(f"Invalid department '{raw_dept}'. Available: {available_codes}")
                all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="department", error_message=f"Department not found. Choose from {available_codes}", raw_value=raw_dept))

            # Validation: semester
            parsed_sem: Optional[int] = None
            if not raw_sem:
                row_errors.append("Semester is required")
                all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="semester", error_message="Semester is required"))
            else:
                try:
                    parsed_sem = int(raw_sem)
                    if parsed_sem < 1 or parsed_sem > 12:
                        row_errors.append("Semester must be between 1 and 12")
                        all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="semester", error_message="Semester must be 1-12", raw_value=raw_sem))
                except ValueError:
                    row_errors.append("Semester must be an integer")
                    all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="semester", error_message="Semester must be an integer", raw_value=raw_sem))

            # Validation: academic_year (YYYY-YYYY)
            if not re.match(r"^\d{4}-\d{4}$", raw_acad_year):
                row_errors.append(f"Academic year must be formatted YYYY-YYYY (got '{raw_acad_year}')")
                all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="academic_year", error_message="Format must be YYYY-YYYY", raw_value=raw_acad_year))

            # Validation: attendance
            parsed_attendance: Optional[float] = None
            if not raw_attendance:
                row_errors.append("Attendance is required")
                all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="attendance", error_message="Attendance is required"))
            else:
                try:
                    parsed_attendance = float(raw_attendance)
                    if parsed_attendance < 0.0 or parsed_attendance > 100.0:
                        row_errors.append("Attendance must be between 0.0 and 100.0")
                        all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="attendance", error_message="Attendance must be 0-100", raw_value=raw_attendance))
                except ValueError:
                    row_errors.append("Attendance must be a valid number")
                    all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="attendance", error_message="Attendance must be a number", raw_value=raw_attendance))

            # Validation: optional numerical bounds
            def parse_num(val_str: str, field_name: str, min_val: float, max_val: float) -> Optional[float]:
                if not val_str:
                    return None
                try:
                    v = float(val_str)
                    if v < min_val or v > max_val:
                        row_errors.append(f"{field_name} must be between {min_val} and {max_val}")
                        all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field=field_name, error_message=f"Must be between {min_val} and {max_val}", raw_value=val_str))
                        return None
                    return v
                except ValueError:
                    row_errors.append(f"{field_name} must be a valid number")
                    all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field=field_name, error_message="Must be a number", raw_value=val_str))
                    return None

            parsed_prev_cgpa = parse_num(raw_prev_cgpa, "previous_cgpa", 0.0, 10.0)
            parsed_mid1 = parse_num(raw_mid1, "mid_1", 0.0, 100.0)
            parsed_mid2 = parse_num(raw_mid2, "mid_2", 0.0, 100.0)
            parsed_internal = parse_num(raw_internal, "internal_marks", 0.0, 100.0)
            parsed_sem_cgpa = parse_num(raw_sem_cgpa, "semester_cgpa", 0.0, 10.0)

            # Validation: backlogs
            parsed_backlogs: int = 0
            if raw_backlogs:
                try:
                    parsed_backlogs = int(raw_backlogs)
                    if parsed_backlogs < 0:
                        row_errors.append("Backlogs cannot be negative")
                        all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="backlogs", error_message="Backlogs cannot be negative", raw_value=raw_backlogs))
                except ValueError:
                    row_errors.append("Backlogs must be an integer")
                    all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="backlogs", error_message="Must be integer", raw_value=raw_backlogs))

            # Check intra-file duplicate
            is_dup_in_file = False
            if raw_student_id and parsed_sem:
                key = (raw_student_id, raw_acad_year, parsed_sem)
                if key in seen_file_keys:
                    is_dup_in_file = True
                    first_row = seen_file_keys[key]
                    err_msg = f"Duplicate entry in CSV: matches row {first_row} for student '{raw_student_id}', term {parsed_sem}"
                    row_errors.append(err_msg)
                    all_errors.append(CSVRowError(row_number=row_idx, student_id=raw_student_id, field="student_id", error_message=err_msg))
                else:
                    seen_file_keys[key] = row_idx

            # Check existing in DB
            is_existing_in_db = False
            if raw_student_id in existing_students:
                is_existing_in_db = True
                if parsed_sem:
                    # Check if term record also exists
                    stu = existing_students[raw_student_id]
                    if any(rec.semester == parsed_sem and rec.academic_year == raw_acad_year for rec in stu.academic_records):
                        # Term record exists in DB
                        pass

            is_valid = len(row_errors) == 0

            preview_items.append(
                CSVPreviewItem(
                    row_number=row_idx,
                    is_valid=is_valid,
                    is_duplicate_in_file=is_dup_in_file,
                    is_existing_in_db=is_existing_in_db,
                    student_id=raw_student_id,
                    name=raw_name,
                    gender=parsed_gender.value,
                    age=parsed_age,
                    department_code=raw_dept,
                    semester=parsed_sem,
                    academic_year=raw_acad_year,
                    attendance=parsed_attendance,
                    previous_cgpa=parsed_prev_cgpa,
                    mid_1=parsed_mid1,
                    mid_2=parsed_mid2,
                    internal_marks=parsed_internal,
                    backlogs=parsed_backlogs,
                    semester_cgpa=parsed_sem_cgpa,
                    grade=raw_grade,
                    historical_risk_level=raw_risk,
                    errors=row_errors
                )
            )

        # 6. Aggregate preview metadata
        total_count = len(preview_items)
        valid_count = sum(1 for item in preview_items if item.is_valid)
        invalid_count = total_count - valid_count
        dup_file_count = sum(1 for item in preview_items if item.is_duplicate_in_file)
        existing_db_count = sum(1 for item in preview_items if item.is_existing_in_db)

        batch_token = str(uuid.uuid4())
        _PREVIEW_STORE[batch_token] = {
            "created_at": datetime.now(timezone.utc),
            "preview_items": preview_items,
            "dept_map": {d.code.upper(): d.id for d in all_depts}
        }

        return CSVValidationPreview(
            import_batch_token=batch_token,
            total_rows=total_count,
            valid_rows_count=valid_count,
            invalid_rows_count=invalid_count,
            duplicate_in_file_count=dup_file_count,
            existing_in_db_count=existing_db_count,
            preview_items=preview_items,
            errors=all_errors,
            is_ready_for_import=valid_count > 0
        )

    @classmethod
    async def commit_csv_import(
        cls,
        db: AsyncSession,
        import_batch_token: str,
        duplicate_policy: ImportDuplicatePolicy = ImportDuplicatePolicy.SKIP_EXISTING
    ) -> CSVImportResult:
        if import_batch_token not in _PREVIEW_STORE:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import batch session expired or not found. Please upload and preview the CSV again."
            )

        batch_data = _PREVIEW_STORE[import_batch_token]
        preview_items: List[CSVPreviewItem] = batch_data["preview_items"]
        dept_map: Dict[str, uuid.UUID] = batch_data["dept_map"]

        valid_items = [item for item in preview_items if item.is_valid]
        if not valid_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid records to import in this batch."
            )

        created_students = 0
        updated_students = 0
        created_records = 0
        updated_records = 0
        skipped_records = 0
        failed_records = 0

        # Execute inside strict atomic transaction
        try:
            # Re-fetch existing students within current transaction
            student_stmt = select(StudentProfile).options(selectinload(StudentProfile.academic_records))
            student_res = await db.execute(student_stmt)
            existing_students_map = {s.student_number: s for s in student_res.scalars().all()}

            for item in valid_items:
                dept_id = dept_map.get(item.department_code.upper())
                if not dept_id:
                    failed_records += 1
                    continue

                student = existing_students_map.get(item.student_id)

                if not student:
                    # Create new StudentProfile
                    enrollment_year = int(item.academic_year.split("-")[0]) if item.academic_year else 2024
                    student = StudentProfile(
                        student_number=item.student_id,
                        name=item.name,
                        gender=GenderEnum(item.gender),
                        age=item.age or 20,
                        department_id=dept_id,
                        enrollment_year=enrollment_year,
                        current_semester=item.semester or 1,
                        cumulative_gpa=item.semester_cgpa or item.previous_cgpa,
                        is_archived=False
                    )
                    db.add(student)
                    await db.flush()
                    existing_students_map[item.student_id] = student
                    created_students += 1

                    # Add new term record directly for new student
                    new_rec = SemesterAcademicRecord(
                        student_id=student.id,
                        academic_year=item.academic_year,
                        semester=item.semester,
                        attendance_percentage=item.attendance,
                        previous_cgpa=item.previous_cgpa,
                        mid_1=item.mid_1,
                        mid_2=item.mid_2,
                        internal_marks=item.internal_marks,
                        backlogs=item.backlogs or 0,
                        semester_cgpa=item.semester_cgpa,
                        grade=item.grade,
                        historical_risk_level=item.historical_risk_level
                    )
                    db.add(new_rec)
                    created_records += 1
                    continue

                # Student profile already exists
                if duplicate_policy == ImportDuplicatePolicy.FAIL_ON_CONFLICT:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Conflict: Student '{item.student_id}' already exists."
                    )
                elif duplicate_policy == ImportDuplicatePolicy.UPDATE_EXISTING:
                    student.name = item.name
                    student.gender = GenderEnum(item.gender)
                    student.age = item.age or student.age
                    student.department_id = dept_id
                    if item.semester and item.semester >= student.current_semester:
                        student.current_semester = item.semester
                        if item.semester_cgpa is not None:
                            student.cumulative_gpa = item.semester_cgpa
                    updated_students += 1

                # Now handle SemesterAcademicRecord for existing student
                existing_rec = next(
                    (r for r in (student.academic_records or []) if r.semester == item.semester and r.academic_year == item.academic_year),
                    None
                )

                if existing_rec:
                    if duplicate_policy == ImportDuplicatePolicy.SKIP_EXISTING:
                        skipped_records += 1
                        continue
                    elif duplicate_policy == ImportDuplicatePolicy.UPDATE_EXISTING:
                        existing_rec.attendance_percentage = item.attendance
                        existing_rec.previous_cgpa = item.previous_cgpa
                        existing_rec.mid_1 = item.mid_1
                        existing_rec.mid_2 = item.mid_2
                        existing_rec.internal_marks = item.internal_marks
                        existing_rec.backlogs = item.backlogs or 0
                        existing_rec.semester_cgpa = item.semester_cgpa
                        existing_rec.grade = item.grade
                        existing_rec.historical_risk_level = item.historical_risk_level
                        updated_records += 1
                else:
                    # Create new term record for existing student
                    new_rec = SemesterAcademicRecord(
                        student_id=student.id,
                        academic_year=item.academic_year,
                        semester=item.semester,
                        attendance_percentage=item.attendance,
                        previous_cgpa=item.previous_cgpa,
                        mid_1=item.mid_1,
                        mid_2=item.mid_2,
                        internal_marks=item.internal_marks,
                        backlogs=item.backlogs or 0,
                        semester_cgpa=item.semester_cgpa,
                        grade=item.grade,
                        historical_risk_level=item.historical_risk_level
                    )
                    db.add(new_rec)
                    created_records += 1

            await db.commit()

            # Clean up preview store
            _PREVIEW_STORE.pop(import_batch_token, None)

            return CSVImportResult(
                total_processed=len(valid_items),
                created_students=created_students,
                updated_students=updated_students,
                created_academic_records=created_records,
                updated_academic_records=updated_records,
                skipped_records=skipped_records,
                failed_records=failed_records,
                duplicate_policy_applied=duplicate_policy,
                message=f"Successfully processed {len(valid_items)} records ({created_students} new students, {created_records} new semester records)."
            )

        except Exception as e:
            await db.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database transaction error during CSV import: {str(e)}"
            )
