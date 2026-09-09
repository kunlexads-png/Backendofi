from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


ByproductType = Literal[
    "Cluster",
    "Cluster Beans",
    "Dust",
    "Nibs",
    "Shaft",
    "FM",
    "Disposed Material"
]


class ByproductBase(BaseModel):
    date: date
    product: ByproductType
    quantity: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)  # in KG
    batch_number: str = Field(..., min_length=2, max_length=50)
    source: str = Field(..., min_length=2, max_length=100)
    sap_batch: Optional[str] = None
    customer: Optional[str] = None
    warehouse_location: str = Field(..., min_length=2, max_length=100)
    status: str = Field(default="Available", max_length=50)
    remarks: Optional[str] = None


class ByproductCreate(ByproductBase):
    pass


class ByproductUpdate(BaseModel):
    date: Optional[date] = None
    product: Optional[ByproductType] = None
    quantity: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    batch_number: Optional[str] = None
    source: Optional[str] = None
    sap_batch: Optional[str] = None
    customer: Optional[str] = None
    warehouse_location: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class ByproductDispose(BaseModel):
    quantity: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)
    reason: str = Field(..., min_length=3)
    authorized_by: Optional[str] = None


class ByproductAdjust(BaseModel):
    new_quantity: float = Field(..., ge=0)
    new_weight: float = Field(..., ge=0)
    reason: str = Field(..., min_length=3)


class ByproductResponse(ByproductBase):
    id: str
    record_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
