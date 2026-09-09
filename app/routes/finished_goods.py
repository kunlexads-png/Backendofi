import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.finished_goods import FinishedGoods
from app.models.user import User, UserRole
from app.models.stock_movement import TransactionType, StockModule
from app.schemas.finished_goods import (
    FinishedGoodsCreate, FinishedGoodsUpdate, FinishedGoodsResponse, FinishedGoodsDispatch
)
from app.auth.dependencies import (
    get_current_user, require_officer, require_supervisor, require_admin
)
from app.services.stock_service import StockService
from app.utils.helpers import generate_unique_id, standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/finished-goods", tags=["Finished Goods Warehouse"])


@router.post("", summary="Add finished goods record")
def create_finished_goods(
    payload: FinishedGoodsCreate,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    record_id = generate_unique_id("FG")

    fg = FinishedGoods(
        record_id=record_id,
        date=payload.date,
        product=payload.product.strip(),
        product_type=payload.product_type.strip(),
        batch_number=payload.batch_number.strip().upper(),
        quantity=payload.quantity,
        number_of_bags=payload.number_of_bags,
        weight=payload.weight,
        warehouse_location=payload.warehouse_location.strip(),
        customer=payload.customer.strip() if payload.customer else None,
        production_date=payload.production_date,
        status=payload.status,
        sap_batch=payload.sap_batch.strip() if payload.sap_batch else None,
        storage_location=payload.storage_location.strip() if payload.storage_location else None,
        remarks=payload.remarks,
        created_by=current_user.username
    )
    db.add(fg)
    db.flush()

    # Automatically record stock IN for Finished Goods
    StockService.record_movement(
        db=db,
        product=fg.product,
        module=StockModule.FINISHED_GOODS,
        transaction_type=TransactionType.IN,
        weight=fg.weight,
        quantity=fg.quantity,
        batch=fg.batch_number,
        reference_number=fg.record_id,
        user=current_user,
        txn_date=fg.date,
        remarks=f"Finished goods {fg.record_id} ({fg.product_type}) added to inventory"
    )

    db.commit()
    db.refresh(fg)
    logger.info(f"Finished Goods created: {fg.record_id} by {current_user.username}")

    return standard_response(
        data=FinishedGoodsResponse.model_validate(fg).model_dump(),
        message="Finished goods record created successfully",
        status_code=status.HTTP_201_CREATED
    )


@router.get("", summary="List finished goods with search and filtering")
def list_finished_goods(
    date_filter: Optional[date] = Query(None, alias="date"),
    product: Optional[str] = Query(None),
    batch: Optional[str] = Query(None),
    customer: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    sap_batch: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FinishedGoods)

    if date_filter:
        query = query.filter(FinishedGoods.date == date_filter)
    if product:
        query = query.filter(FinishedGoods.product.ilike(f"%{product}%"))
    if batch:
        query = query.filter(FinishedGoods.batch_number.ilike(f"%{batch}%"))
    if customer:
        query = query.filter(FinishedGoods.customer.ilike(f"%{customer}%"))
    if status_filter:
        query = query.filter(FinishedGoods.status == status_filter)
    if sap_batch:
        query = query.filter(FinishedGoods.sap_batch.ilike(f"%{sap_batch}%"))

    total = query.count()
    records = (
        query.order_by(FinishedGoods.date.desc(), FinishedGoods.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [FinishedGoodsResponse.model_validate(r).model_dump() for r in records]

    return standard_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        },
        message="Finished goods records retrieved successfully"
    )


@router.get("/{id}", summary="Get finished goods record by ID")
def get_finished_goods(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fg = db.query(FinishedGoods).filter(
        (FinishedGoods.id == id) | (FinishedGoods.record_id == id)
    ).first()
    if not fg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finished goods record not found"
        )
    return standard_response(
        data=FinishedGoodsResponse.model_validate(fg).model_dump(),
        message="Finished goods details retrieved"
    )


@router.put("/{id}", summary="Update finished goods record")
def update_finished_goods(
    id: str,
    payload: FinishedGoodsUpdate,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    fg = db.query(FinishedGoods).filter(
        (FinishedGoods.id == id) | (FinishedGoods.record_id == id)
    ).first()
    if not fg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finished goods record not found"
        )

    for field in [
        "date", "product", "product_type", "batch_number", "quantity",
        "number_of_bags", "weight", "warehouse_location", "customer",
        "production_date", "status", "sap_batch", "storage_location", "remarks"
    ]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(fg, field, val)

    db.commit()
    db.refresh(fg)
    logger.info(f"Finished Goods {fg.record_id} updated by {current_user.username}")

    return standard_response(
        data=FinishedGoodsResponse.model_validate(fg).model_dump(),
        message="Finished goods record updated successfully"
    )


@router.post("/{id}/dispatch", summary="Dispatch finished goods (Records stock OUT)")
def dispatch_finished_goods(
    id: str,
    payload: FinishedGoodsDispatch,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    fg = db.query(FinishedGoods).filter(
        (FinishedGoods.id == id) | (FinishedGoods.record_id == id)
    ).first()
    if not fg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finished goods record not found"
        )

    # Record stock OUT movement
    StockService.record_movement(
        db=db,
        product=fg.product,
        module=StockModule.FINISHED_GOODS,
        transaction_type=TransactionType.OUT,
        weight=payload.weight,
        quantity=payload.quantity,
        batch=fg.batch_number,
        reference_number=payload.reference_number,
        user=current_user,
        remarks=f"Dispatched to customer {payload.customer}. {payload.remarks or ''}"
    )

    fg.status = "Dispatched"
    fg.customer = payload.customer
    db.commit()
    db.refresh(fg)

    return standard_response(
        data=FinishedGoodsResponse.model_validate(fg).model_dump(),
        message=f"Dispatched {payload.weight}kg of {fg.product} to {payload.customer}"
    )


@router.delete("/{id}", summary="Delete finished goods record (Admin only)")
def delete_finished_goods(
    id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    fg = db.query(FinishedGoods).filter(
        (FinishedGoods.id == id) | (FinishedGoods.record_id == id)
    ).first()
    if not fg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finished goods record not found"
        )
    db.delete(fg)
    db.commit()
    logger.info(f"Finished Goods {fg.record_id} deleted by {current_user.username}")

    return standard_response(
        data=None,
        message="Finished goods record deleted successfully"
    )
