import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.byproduct import Byproduct, BYPRODUCT_PRODUCTS
from app.models.user import User, UserRole
from app.models.stock_movement import TransactionType, StockModule
from app.schemas.byproduct import (
    ByproductCreate, ByproductUpdate, ByproductResponse,
    ByproductDispose, ByproductAdjust, ByproductType
)
from app.auth.dependencies import (
    get_current_user, require_officer, require_supervisor, require_admin
)
from app.services.stock_service import StockService
from app.utils.helpers import generate_unique_id, standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/byproducts", tags=["By-product Warehouse"])


@router.post("", summary="Add by-product stock record")
def create_byproduct(
    payload: ByproductCreate,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    record_id = generate_unique_id("BP")

    bp = Byproduct(
        record_id=record_id,
        date=payload.date,
        product=payload.product,
        quantity=payload.quantity,
        weight=payload.weight,
        batch_number=payload.batch_number.strip().upper(),
        source=payload.source.strip(),
        sap_batch=payload.sap_batch.strip() if payload.sap_batch else None,
        customer=payload.customer.strip() if payload.customer else None,
        warehouse_location=payload.warehouse_location.strip(),
        status=payload.status,
        remarks=payload.remarks,
        created_by=current_user.username
    )
    db.add(bp)
    db.flush()

    # Automatically record stock IN for Byproduct
    StockService.record_movement(
        db=db,
        product=bp.product,
        module=StockModule.BYPRODUCT,
        transaction_type=TransactionType.IN,
        weight=bp.weight,
        quantity=bp.quantity,
        batch=bp.batch_number,
        reference_number=bp.record_id,
        user=current_user,
        txn_date=bp.date,
        remarks=f"By-product {bp.record_id} ({bp.product}) added from source {bp.source}"
    )

    db.commit()
    db.refresh(bp)
    logger.info(f"Byproduct created: {bp.record_id} ({bp.product}) by {current_user.username}")

    return standard_response(
        data=ByproductResponse.model_validate(bp).model_dump(),
        message="By-product record created successfully",
        status_code=status.HTTP_201_CREATED
    )


@router.get("", summary="List by-products with search and filtering")
def list_byproducts(
    product: Optional[str] = Query(None, description="Filter by product type (Dust, Nibs, Cluster, etc.)"),
    date_filter: Optional[date] = Query(None, alias="date"),
    batch: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Byproduct)

    if product:
        query = query.filter(Byproduct.product.ilike(f"%{product}%"))
    if date_filter:
        query = query.filter(Byproduct.date == date_filter)
    if batch:
        query = query.filter(Byproduct.batch_number.ilike(f"%{batch}%"))
    if status_filter:
        query = query.filter(Byproduct.status == status_filter)
    if source:
        query = query.filter(Byproduct.source.ilike(f"%{source}%"))

    total = query.count()
    records = (
        query.order_by(Byproduct.date.desc(), Byproduct.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [ByproductResponse.model_validate(r).model_dump() for r in records]

    return standard_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        },
        message="By-product records retrieved successfully"
    )


@router.get("/balance", summary="Get real-time by-product stock balances")
def get_byproducts_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    balances = {}
    for p in BYPRODUCT_PRODUCTS:
        balances[p] = StockService.get_current_product_balance(db, p, StockModule.BYPRODUCT)

    return standard_response(
        data={
            "balances": balances,
            "unit": "KG",
            "as_of": str(date.today())
        },
        message="By-product stock balances retrieved"
    )


@router.get("/{id}", summary="Get by-product record by ID")
def get_byproduct(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bp = db.query(Byproduct).filter(
        (Byproduct.id == id) | (Byproduct.record_id == id)
    ).first()
    if not bp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="By-product record not found"
        )
    return standard_response(
        data=ByproductResponse.model_validate(bp).model_dump(),
        message="By-product details retrieved"
    )


@router.put("/{id}", summary="Update by-product record")
def update_byproduct(
    id: str,
    payload: ByproductUpdate,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    bp = db.query(Byproduct).filter(
        (Byproduct.id == id) | (Byproduct.record_id == id)
    ).first()
    if not bp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="By-product record not found"
        )

    for field in [
        "date", "product", "quantity", "weight", "batch_number",
        "source", "sap_batch", "customer", "warehouse_location",
        "status", "remarks"
    ]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(bp, field, val)

    db.commit()
    db.refresh(bp)
    logger.info(f"Byproduct {bp.record_id} updated by {current_user.username}")

    return standard_response(
        data=ByproductResponse.model_validate(bp).model_dump(),
        message="By-product record updated successfully"
    )


@router.post("/{id}/dispose", summary="Dispose by-product material")
def dispose_byproduct(
    id: str,
    payload: ByproductDispose,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Records a DISPOSAL transaction for degraded, contaminated, or scrap by-product material.
    """
    bp = db.query(Byproduct).filter(
        (Byproduct.id == id) | (Byproduct.record_id == id)
    ).first()
    if not bp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="By-product record not found"
        )

    # Record stock DISPOSAL
    StockService.record_movement(
        db=db,
        product=bp.product,
        module=StockModule.BYPRODUCT,
        transaction_type=TransactionType.DISPOSAL,
        weight=payload.weight,
        quantity=payload.quantity,
        batch=bp.batch_number,
        reference_number=bp.record_id,
        user=current_user,
        remarks=f"Disposed: {payload.reason}"
    )

    bp.status = "Disposed"
    bp.remarks = f"{bp.remarks or ''} | Disposed {payload.weight}kg on {date.today()}: {payload.reason}".strip(" |")
    db.commit()
    db.refresh(bp)

    return standard_response(
        data=ByproductResponse.model_validate(bp).model_dump(),
        message=f"Disposed {payload.weight}kg of {bp.product} successfully"
    )


@router.post("/{id}/adjust", summary="Adjust by-product stock (Admin/Supervisor)")
def adjust_byproduct(
    id: str,
    payload: ByproductAdjust,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    bp = db.query(Byproduct).filter(
        (Byproduct.id == id) | (Byproduct.record_id == id)
    ).first()
    if not bp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="By-product record not found"
        )

    weight_diff = payload.new_weight - bp.weight
    qty_diff = payload.new_quantity - bp.quantity

    if weight_diff != 0:
        StockService.record_movement(
            db=db,
            product=bp.product,
            module=StockModule.BYPRODUCT,
            transaction_type=TransactionType.ADJUSTMENT,
            weight=abs(weight_diff),
            quantity=abs(qty_diff),
            batch=bp.batch_number,
            reference_number=bp.record_id,
            user=current_user,
            remarks=f"Physical stock count adjustment: {payload.reason} (Delta: {weight_diff}kg)",
            allow_negative=(current_user.role == UserRole.ADMIN)
        )

    bp.weight = payload.new_weight
    bp.quantity = payload.new_quantity
    bp.remarks = f"{bp.remarks or ''} | Adjusted on {date.today()}: {payload.reason}".strip(" |")
    db.commit()
    db.refresh(bp)

    return standard_response(
        data=ByproductResponse.model_validate(bp).model_dump(),
        message=f"Adjusted {bp.product} stock to {payload.new_weight}kg"
    )


@router.delete("/{id}", summary="Delete by-product record (Admin only)")
def delete_byproduct(
    id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    bp = db.query(Byproduct).filter(
        (Byproduct.id == id) | (Byproduct.record_id == id)
    ).first()
    if not bp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="By-product record not found"
        )
    db.delete(bp)
    db.commit()
    logger.info(f"Byproduct {bp.record_id} deleted by {current_user.username}")

    return standard_response(
        data=None,
        message="By-product record deleted successfully"
    )
