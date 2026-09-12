import enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ImportDuplicatePolicy(str, enum.Enum):
    SKIP_EXISTING = "SKIP_EXISTING"
    UPDATE_EXISTING = "UPDATE_EXISTING"
    FAIL_ON_CONFLICT = "FAIL_ON_CONFLICT"


class CSVRowError(BaseModel):
    row_number: int
    student_id: Optional[str] = None
    field: str
    error_message: str
    raw_value: Optional[str] = None


class CSVPreviewItem(BaseModel):
    row_number: int
    is_valid: bool
    is_duplicate_in_file: bool = False
    is_existing_in_db: bool = False
    student_id: str
    name: str
    gender: str
    age: Optional[int] = None
    department_code: str
    semester: Optional[int] = None
    academic_year: str
    attendance: Optional[float] = None
    previous_cgpa: Optional[float] = None
    mid_1: Optional[float] = None
    mid_2: Optional[float] = None
    internal_marks: Optional[float] = None
    backlogs: Optional[int] = None
    semester_cgpa: Optional[float] = None
    grade: Optional[str] = None
    historical_risk_level: Optional[str] = None
    errors: List[str] = []


class CSVValidationPreview(BaseModel):
    import_batch_token: str
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    duplicate_in_file_count: int
    existing_in_db_count: int
    preview_items: List[CSVPreviewItem]
    errors: List[CSVRowError]
    is_ready_for_import: bool


class CSVImportConfirmRequest(BaseModel):
    import_batch_token: str
    duplicate_policy: ImportDuplicatePolicy = ImportDuplicatePolicy.SKIP_EXISTING


class CSVImportResult(BaseModel):
    total_processed: int
    created_students: int
    updated_students: int
    created_academic_records: int
    updated_academic_records: int
    skipped_records: int
    failed_records: int
    duplicate_policy_applied: ImportDuplicatePolicy
    message: str
