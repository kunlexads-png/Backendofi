import random
import string
from datetime import datetime, date, timedelta
from typing import Any, Optional
from fastapi.responses import JSONResponse


def generate_unique_id(prefix: str) -> str:
    """Generates a human-readable unique identifier, e.g. ARR-2026-A8K2"""
    current_year = datetime.utcnow().year
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{current_year}-{random_part}"


def standard_response(
    data: Any = None,
    message: str = "Operation successful",
    success: bool = True,
    error_code: Optional[str] = None,
    error_details: Any = None,
    status_code: int = 200
) -> JSONResponse:
    """Generates standardized API JSON response."""
    payload = {
        "success": success,
        "message": message,
        "data": data,
        "error": {
            "code": error_code,
            "details": error_details
        } if not success or error_code else None
    }
    return JSONResponse(status_code=status_code, content=payload)


def get_date_bounds():
    """Returns today, start of week, and start of month dates."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    return today, start_of_week, start_of_month
