from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.arrival import ArrivalStatus


class ArrivalBase(BaseModel):
    date: date
    time: str = Field(..., description="Time string HH:MM", pattern=r"^\d{2}:\d{2}$")
    truck_number: str = Field(..., min_length=2, max_length=50)
    driver_name: str = Field(..., min_length=2, max_length=100)
    supplier: str = Field(..., min_length=2, max_length=150)
    customer: Optional[str] = None
    product: str = Field(default="Cocoa Beans", max_length=100)
    number_of_bags: int = Field(..., gt=0)
    gross_weight: float = Field(..., gt=0)
    tare_weight: float = Field(..., ge=0)
    net_weight: Optional[float] = None
    batch_number: str = Field(..., min_length=2, max_length=50)
    warehouse: str = Field(..., min_length=2, max_length=100)
    cluster: str = Field(..., min_length=1, max_length=100)
    moisture: float = Field(..., ge=0, le=100, description="Moisture percentage")
    status: ArrivalStatus = ArrivalStatus.PENDING
    offloading_status: str = Field(default="Not Started", max_length=50)
    remarks: Optional[str] = None


class ArrivalCreate(ArrivalBase):
    pass


class ArrivalUpdate(BaseModel):
    date: Optional[date] = None
    time: Optional[str] = None
    truck_number: Optional[str] = None
    driver_name: Optional[str] = None
    supplier: Optional[str] = None
    customer: Optional[str] = None
    product: Optional[str] = None
    number_of_bags: Optional[int] = Field(None, gt=0)
    gross_weight: Optional[float] = Field(None, gt=0)
    tare_weight: Optional[float] = Field(None, ge=0)
    net_weight: Optional[float] = None
    batch_number: Optional[str] = None
    warehouse: Optional[str] = None
    cluster: Optional[str] = None
    moisture: Optional[float] = Field(None, ge=0, le=100)
    status: Optional[ArrivalStatus] = None
    offloading_status: Optional[str] = None
    remarks: Optional[str] = None


class ArrivalResponse(ArrivalBase):
    id: str
    arrival_id: str
    net_weight: float
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
