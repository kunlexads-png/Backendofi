import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.stock_movement import StockMovement, TransactionType, StockModule
from app.models.user import User, UserRole
from app.schemas.stock import (
    StockMovementCreate, StockMovementResponse, StockAdjustmentRequest, StockSummaryResponse
)
from app.auth.dependencies import (
    get_current_user, require_supervisor, require_admin
)
from app.services.stock_service import StockService
from app.utils.helpers import generate_unique_id, standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stock", tags=["Stock Management"])


@router.get("/summary", summary="Get comprehensive stock balances and breakdown")
def get_stock_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns total cocoa stock, total finished goods stock, total by-product stock,
    breakdown for Dust, Nibs, Cluster, Shaft, FM, etc., and detailed ledger rows.
    """
    summary = StockService.get_stock_summary(db)
    return standard_response(
        data=summary,
        message="Stock summary retrieved successfully"
    )


@router.get("/movements", summary="List centralized stock transactions")
def list_stock_movements(
    product: Optional[str] = Query(None),
    module: Optional[StockModule] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    batch: Optional[str] = Query(None),
    date_filter: Optional[date] = Query(None, alias="date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(StockMovement)

    if product:
        query = query.filter(StockMovement.product.ilike(f"%{product}%"))
    if module:
        query = query.filter(StockMovement.module == module)
    if transaction_type:
        query = query.filter(StockMovement.transaction_type == transaction_type)
    if batch:
        query = query.filter(StockMovement.batch.ilike(f"%{batch}%"))
    if date_filter:
        query = query.filter(StockMovement.date == date_filter)

    total = query.count()
    records = (
        query.order_by(StockMovement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [StockMovementResponse.model_validate(r).model_dump() for r in records]

    return standard_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        },
        message="Stock movements retrieved successfully"
    )


@router.post("/adjust", summary="Perform manual inventory stock adjustment")
def perform_stock_adjustment(
    payload: StockAdjustmentRequest,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Records an inventory adjustment.
    If allow_negative is True, requires explicit Admin role.
    """
    if payload.allow_negative and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins can authorize negative stock balance adjustments."
        )

    movement = StockService.record_movement(
        db=db,
        product=payload.product,
        module=payload.module,
        transaction_type=TransactionType.ADJUSTMENT,
        weight=payload.adjustment_weight,
        quantity=payload.adjustment_quantity,
        batch=payload.batch,
        reference_number=f"ADJ-{payload.batch}",
        user=current_user,
        remarks=f"Manual Adjustment: {payload.reason}",
        allow_negative=payload.allow_negative
    )
    db.commit()
    db.refresh(movement)

    logger.info(f"Stock adjusted for {payload.product} by {current_user.username}")

    return standard_response(
        data=StockMovementResponse.model_validate(movement).model_dump(),
        message=f"Stock adjusted for {payload.product}. New balance: {movement.new_balance}kg"
    )
