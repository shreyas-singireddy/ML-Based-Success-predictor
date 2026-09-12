from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.deps import require_roles
from backend.app.models.user import User, UserRole
from backend.app.schemas.csv_import import (
    CSVValidationPreview,
    CSVImportConfirmRequest,
    CSVImportResult
)
from backend.app.services.csv_service import CSVService

router = APIRouter(prefix="/students/import", tags=["CSV Bulk Import"])


@router.post("/validate", response_model=CSVValidationPreview)
async def validate_csv(
    file: UploadFile = File(..., description="CSV file with student records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    """
    Step 1: Upload and validate CSV file.
    Parses all rows, verifies column headers, data types, value boundaries,
    detects intra-file duplicates and conflicts with database,
    and returns an interactive preview with line-level errors without modifying the database.
    """
    preview = await CSVService.parse_and_preview_csv(db, file)
    return preview


@router.post("/confirm", response_model=CSVImportResult, status_code=status.HTTP_200_OK)
async def confirm_import(
    request_in: CSVImportConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY))
):
    """
    Step 2: Explicitly confirm import of validated batch.
    Executes an atomic database transaction. Commits valid student profiles and semester records.
    Applies the chosen duplicate policy (SKIP_EXISTING, UPDATE_EXISTING, FAIL_ON_CONFLICT).
    """
    result = await CSVService.commit_csv_import(
        db=db,
        import_batch_token=request_in.import_batch_token,
        duplicate_policy=request_in.duplicate_policy
    )
    return result
