import os
from fastapi import HTTPException, status
from app.config import settings

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "pdf", "jpg", "jpeg", "png"}


def validate_file_extension(filename: str) -> str:
    """Validates that the file has a permitted extension and returns the extension."""
    if "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no extension"
        )
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def validate_file_size(size_bytes: int) -> None:
    """Validates that the uploaded file does not exceed the maximum allowed size."""
    if size_bytes > settings.MAX_FILE_SIZE_BYTES:
        max_mb = settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_mb}MB"
        )


def validate_weights(gross_weight: float, tare_weight: float) -> float:
    """Validates gross and tare weights and returns the calculated net weight."""
    if gross_weight <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Gross weight must be greater than zero"
        )
    if tare_weight < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tare weight cannot be negative"
        )
    if gross_weight < tare_weight:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Gross weight cannot be less than tare weight"
        )
    return round(gross_weight - tare_weight, 2)


def validate_moisture(moisture: float) -> None:
    """Validates cocoa bean moisture content percentage."""
    if moisture < 0 or moisture > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Moisture must be between 0% and 100%"
        )
