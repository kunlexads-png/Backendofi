from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.stock_movement import TransactionType, StockModule


class StockMovementBase(BaseModel):
    product: str = Field(..., min_length=2)
    module: StockModule
    transaction_type: TransactionType
    quantity: float = Field(default=0.0, ge=0)
    weight: float = Field(..., description="Weight in KG or MT")
    batch: str = Field(..., min_length=2)
    reference_number: str = Field(..., min_length=2)
    remarks: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    pass


class StockAdjustmentRequest(BaseModel):
    product: str = Field(..., min_length=2)
    module: StockModule
    batch: str = Field(..., min_length=2)
    adjustment_weight: float = Field(..., description="Positive to add, negative to reduce")
    adjustment_quantity: float = Field(default=0.0)
    reason: str = Field(..., min_length=5)
    allow_negative: bool = Field(default=False, description="Admin explicit authorization only")


class StockMovementResponse(StockMovementBase):
    id: str
    transaction_id: str
    previous_balance: float
    new_balance: float
    user: str
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class StockBalance(BaseModel):
    product: str
    module: str
    opening_stock: float = 0.0
    stock_in: float = 0.0
    stock_out: float = 0.0
    disposal: float = 0.0
    adjustments: float = 0.0
    closing_stock: float = 0.0
    unit: str = "KG"


class StockSummaryResponse(BaseModel):
    total_cocoa_stock: float
    total_finished_goods_stock: float
    total_byproduct_stock: float
    byproducts_breakdown: dict[str, float]
    balances: list[StockBalance]
