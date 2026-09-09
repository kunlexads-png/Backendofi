from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class FinishedGoodsBase(BaseModel):
    date: date
    product: str = Field(..., min_length=2, max_length=100)
    product_type: str = Field(..., min_length=2, max_length=100)
    batch_number: str = Field(..., min_length=2, max_length=50)
    quantity: float = Field(..., gt=0)
    number_of_bags: int = Field(default=0, ge=0)
    weight: float = Field(..., gt=0)
    warehouse_location: str = Field(..., min_length=2, max_length=100)
    customer: Optional[str] = None
    production_date: Optional[date] = None
    status: str = Field(default="In Stock", max_length=50)
    sap_batch: Optional[str] = None
    storage_location: Optional[str] = None
    remarks: Optional[str] = None


class FinishedGoodsCreate(FinishedGoodsBase):
    pass


class FinishedGoodsUpdate(BaseModel):
    date: Optional[date] = None
    product: Optional[str] = None
    product_type: Optional[str] = None
    batch_number: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    number_of_bags: Optional[int] = Field(None, ge=0)
    weight: Optional[float] = Field(None, gt=0)
    warehouse_location: Optional[str] = None
    customer: Optional[str] = None
    production_date: Optional[date] = None
    status: Optional[str] = None
    sap_batch: Optional[str] = None
    storage_location: Optional[str] = None
    remarks: Optional[str] = None


class FinishedGoodsDispatch(BaseModel):
    quantity: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)
    customer: str = Field(..., min_length=2)
    reference_number: str = Field(..., min_length=2)
    remarks: Optional[str] = None


class FinishedGoodsResponse(FinishedGoodsBase):
    id: str
    record_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
