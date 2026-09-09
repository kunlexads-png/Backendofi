from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    details: Any = None


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    error: Optional[ErrorDetail] = None
