import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.arrival import Arrival, ArrivalStatus
from app.models.user import User, UserRole
from app.models.stock_movement import TransactionType, StockModule
from app.schemas.arrival import ArrivalCreate, ArrivalUpdate, ArrivalResponse
from app.auth.dependencies import (
    get_current_user, require_officer, require_supervisor, require_admin
)
from app.services.stock_service import StockService
from app.utils.validators import validate_weights, validate_moisture
from app.utils.helpers import generate_unique_id, standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/arrivals", tags=["Cocoa Arrivals"])


@router.post("", summary="Record new cocoa arrival at warehouse")
def create_arrival(
    payload: ArrivalCreate,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    """
    Creates a new arrival entry for cocoa received.
    Automatically verifies weights and calculates net weight.
    If arrival is marked Completed, immediately updates the centralized cocoa stock ledger.
    """
    net_weight = validate_weights(payload.gross_weight, payload.tare_weight)
    validate_moisture(payload.moisture)

    arrival_id = generate_unique_id("ARR")

    new_arrival = Arrival(
        arrival_id=arrival_id,
        date=payload.date,
        time=payload.time,
        truck_number=payload.truck_number.strip().upper(),
        driver_name=payload.driver_name.strip(),
        supplier=payload.supplier.strip(),
        customer=payload.customer.strip() if payload.customer else None,
        product=payload.product.strip(),
        number_of_bags=payload.number_of_bags,
        gross_weight=payload.gross_weight,
        tare_weight=payload.tare_weight,
        net_weight=net_weight,
        batch_number=payload.batch_number.strip().upper(),
        warehouse=payload.warehouse.strip(),
        cluster=payload.cluster.strip(),
        moisture=payload.moisture,
        status=payload.status,
        offloading_status=payload.offloading_status,
        remarks=payload.remarks,
        created_by=current_user.username
    )
    db.add(new_arrival)
    db.flush()

    # If status is already Completed, log stock IN movement
    if new_arrival.status == ArrivalStatus.COMPLETED:
        StockService.record_movement(
            db=db,
            product=new_arrival.product,
            module=StockModule.ARRIVAL,
            transaction_type=TransactionType.IN,
            weight=new_arrival.net_weight,
            quantity=float(new_arrival.number_of_bags),
            batch=new_arrival.batch_number,
            reference_number=new_arrival.arrival_id,
            user=current_user,
            txn_date=new_arrival.date,
            remarks=f"Arrival {new_arrival.arrival_id} offloaded from truck {new_arrival.truck_number}"
        )

    db.commit()
    db.refresh(new_arrival)
    logger.info(f"Arrival created: {new_arrival.arrival_id} by {current_user.username}")

    return standard_response(
        data=ArrivalResponse.model_validate(new_arrival).model_dump(),
        message="Arrival record created successfully",
        status_code=status.HTTP_201_CREATED
    )


@router.get("", summary="List arrivals with search and filtering")
def list_arrivals(
    date_filter: Optional[date] = Query(None, alias="date", description="Filter by date YYYY-MM-DD"),
    supplier: Optional[str] = Query(None, description="Search by supplier name"),
    customer: Optional[str] = Query(None, description="Search by customer name"),
    batch: Optional[str] = Query(None, description="Filter by batch number"),
    truck: Optional[str] = Query(None, description="Filter by truck number"),
    status_filter: Optional[ArrivalStatus] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Arrival)

    if date_filter:
        query = query.filter(Arrival.date == date_filter)
    if supplier:
        query = query.filter(Arrival.supplier.ilike(f"%{supplier}%"))
    if customer:
        query = query.filter(Arrival.customer.ilike(f"%{customer}%"))
    if batch:
        query = query.filter(Arrival.batch_number.ilike(f"%{batch}%"))
    if truck:
        query = query.filter(Arrival.truck_number.ilike(f"%{truck}%"))
    if status_filter:
        query = query.filter(Arrival.status == status_filter)

    total = query.count()
    records = (
        query.order_by(Arrival.date.desc(), Arrival.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [ArrivalResponse.model_validate(r).model_dump() for r in records]
    return standard_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        },
        message="Arrival records retrieved successfully"
    )


@router.get("/{id}", summary="Get arrival record details by ID")
def get_arrival(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    arrival = db.query(Arrival).filter(
        (Arrival.id == id) | (Arrival.arrival_id == id)
    ).first()
    if not arrival:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arrival record not found"
        )
    return standard_response(
        data=ArrivalResponse.model_validate(arrival).model_dump(),
        message="Arrival details retrieved"
    )


@router.put("/{id}", summary="Update arrival record")
def update_arrival(
    id: str,
    payload: ArrivalUpdate,
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    arrival = db.query(Arrival).filter(
        (Arrival.id == id) | (Arrival.arrival_id == id)
    ).first()
    if not arrival:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arrival record not found"
        )

    previous_status = arrival.status

    if payload.gross_weight is not None or payload.tare_weight is not None:
        gross = payload.gross_weight if payload.gross_weight is not None else arrival.gross_weight
        tare = payload.tare_weight if payload.tare_weight is not None else arrival.tare_weight
        arrival.net_weight = validate_weights(gross, tare)
        arrival.gross_weight = gross
        arrival.tare_weight = tare

    if payload.moisture is not None:
        validate_moisture(payload.moisture)
        arrival.moisture = payload.moisture

    for field in [
        "date", "time", "truck_number", "driver_name", "supplier",
        "customer", "product", "number_of_bags", "batch_number",
        "warehouse", "cluster", "status", "offloading_status", "remarks"
    ]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(arrival, field, val)

    # Check if newly marked COMPLETED
    if previous_status != ArrivalStatus.COMPLETED and arrival.status == ArrivalStatus.COMPLETED:
        StockService.record_movement(
            db=db,
            product=arrival.product,
            module=StockModule.ARRIVAL,
            transaction_type=TransactionType.IN,
            weight=arrival.net_weight,
            quantity=float(arrival.number_of_bags),
            batch=arrival.batch_number,
            reference_number=arrival.arrival_id,
            user=current_user,
            txn_date=arrival.date,
            remarks=f"Arrival {arrival.arrival_id} marked Completed by {current_user.username}"
        )

    db.commit()
    db.refresh(arrival)
    logger.info(f"Arrival {arrival.arrival_id} updated by {current_user.username}")

    return standard_response(
        data=ArrivalResponse.model_validate(arrival).model_dump(),
        message="Arrival record updated successfully"
    )


@router.delete("/{id}", summary="Delete arrival record (Admin only)")
def delete_arrival(
    id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    arrival = db.query(Arrival).filter(
        (Arrival.id == id) | (Arrival.arrival_id == id)
    ).first()
    if not arrival:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arrival record not found"
        )
    db.delete(arrival)
    db.commit()
    logger.info(f"Arrival {arrival.arrival_id} deleted by {current_user.username}")

    return standard_response(
        data=None,
        message="Arrival record deleted successfully"
    )
