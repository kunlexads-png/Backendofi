import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.uploaded_file import UploadedFile
from app.models.arrival import Arrival, ArrivalStatus
from app.models.finished_goods import FinishedGoods
from app.models.byproduct import Byproduct
from app.models.user import User
from app.auth.dependencies import get_current_user, require_officer
from app.services.file_service import FileService
from app.services.stock_service import StockService
from app.models.stock_movement import TransactionType, StockModule
from app.utils.helpers import generate_unique_id, standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uploads", tags=["File Uploads"])


@router.post("", summary="Upload CSV, XLSX, XLS, PDF, or image file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    """
    Validates file extension and size, stores it securely, extracts structured
    information, and returns parsed preview data for human review before DB insertion.
    """
    db_file = await FileService.save_uploaded_file(db, file, current_user)
    
    parsed_preview = None
    if db_file.extracted_data:
        try:
            parsed_preview = json.loads(db_file.extracted_data)
        except Exception:
            parsed_preview = {"raw": db_file.extracted_data}

    return standard_response(
        data={
            "id": db_file.id,
            "filename": db_file.filename,
            "original_filename": db_file.original_filename,
            "file_type": db_file.file_type,
            "file_size": db_file.file_size,
            "status": db_file.status,
            "created_by": db_file.created_by,
            "created_at": db_file.created_at.isoformat(),
            "preview_data": parsed_preview
        },
        message="File uploaded and analyzed successfully",
        status_code=status.HTTP_201_CREATED
    )


@router.get("", summary="List uploaded files history")
def list_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(UploadedFile)
    total = query.count()
    records = query.order_by(UploadedFile.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for r in records:
        preview = None
        if r.extracted_data:
            try:
                preview = json.loads(r.extracted_data)
            except Exception:
                preview = {"raw": r.extracted_data}
        items.append({
            "id": r.id,
            "filename": r.filename,
            "original_filename": r.original_filename,
            "file_type": r.file_type,
            "file_size": r.file_size,
            "status": r.status,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat(),
            "preview_summary": {
                "total_rows": preview.get("total_rows") if isinstance(preview, dict) else None,
                "valid_count": preview.get("valid_count") if isinstance(preview, dict) else None
            }
        })

    return standard_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        },
        message="Upload history retrieved"
    )


@router.get("/{id}", summary="Get uploaded file extraction details")
def get_upload_details(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upload = db.query(UploadedFile).filter(UploadedFile.id == id).first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file not found"
        )

    parsed = None
    if upload.extracted_data:
        try:
            parsed = json.loads(upload.extracted_data)
        except Exception:
            parsed = {"raw": upload.extracted_data}

    return standard_response(
        data={
            "id": upload.id,
            "filename": upload.filename,
            "original_filename": upload.original_filename,
            "file_type": upload.file_type,
            "file_size": upload.file_size,
            "status": upload.status,
            "created_by": upload.created_by,
            "created_at": upload.created_at.isoformat(),
            "extracted_data": parsed,
            "error_message": upload.error_message
        },
        message="File extraction details retrieved"
    )


@router.post("/{id}/import", summary="Confirm and import reviewed data into warehouse database")
def import_reviewed_data(
    id: str,
    target_module: str = Query(..., description="Target: arrival, finished_goods, or byproduct"),
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    """
    Imports the reviewed rows from the parsed file into the chosen target warehouse module.
    Prevents automatic or uncertain AI insertions without human review.
    """
    upload = db.query(UploadedFile).filter(UploadedFile.id == id).first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file not found"
        )

    if not upload.extracted_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extracted data available in this file to import"
        )

    try:
        parsed = json.loads(upload.extracted_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupt extracted data format"
        )

    valid_rows = parsed.get("valid_rows", [])
    if not valid_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid rows available to import"
        )

    imported_count = 0
    from datetime import date as dt_date

    for row_obj in valid_rows:
        row = row_obj.get("data", {})
        try:
            if target_module.lower() == "arrival":
                arr = Arrival(
                    arrival_id=generate_unique_id("ARR"),
                    date=dt_date.today(),
                    time=row.get("time", "08:00"),
                    truck_number=str(row.get("truck_number", row.get("truck", "TRK-001"))).upper(),
                    driver_name=str(row.get("driver_name", row.get("driver", "Unknown Driver"))),
                    supplier=str(row.get("supplier", "OFI Partner")),
                    customer=str(row.get("customer", "")) or None,
                    product=str(row.get("product", "Cocoa Beans")),
                    number_of_bags=int(float(row.get("number_of_bags", row.get("bags", 100)))),
                    gross_weight=float(row.get("gross_weight", row.get("weight", 6500.0))),
                    tare_weight=float(row.get("tare_weight", 500.0)),
                    net_weight=float(row.get("net_weight", 6000.0)),
                    batch_number=str(row.get("batch_number", row.get("batch", "B-2026"))).upper(),
                    warehouse=str(row.get("warehouse", "Main Warehouse A")),
                    cluster=str(row.get("cluster", "Cluster 1")),
                    moisture=float(row.get("moisture", 7.5)),
                    status=ArrivalStatus.ARRIVED,
                    offloading_status="Waiting",
                    remarks=f"Imported from {upload.original_filename}",
                    created_by=current_user.username
                )
                db.add(arr)
                imported_count += 1
            elif target_module.lower() in ("finished_goods", "finished-goods"):
                fg = FinishedGoods(
                    record_id=generate_unique_id("FG"),
                    date=dt_date.today(),
                    product=str(row.get("product", "Cocoa Butter")),
                    product_type=str(row.get("product_type", "Natural")),
                    batch_number=str(row.get("batch_number", row.get("batch", "FG-B-2026"))).upper(),
                    quantity=float(row.get("quantity", 50.0)),
                    number_of_bags=int(float(row.get("number_of_bags", row.get("bags", 50)))),
                    weight=float(row.get("weight", 2500.0)),
                    warehouse_location=str(row.get("warehouse_location", "Bay 3")),
                    status="In Stock",
                    created_by=current_user.username
                )
                db.add(fg)
                imported_count += 1
            elif target_module.lower() == "byproduct":
                bp = Byproduct(
                    record_id=generate_unique_id("BP"),
                    date=dt_date.today(),
                    product=str(row.get("product", "Dust")),
                    quantity=float(row.get("quantity", 20.0)),
                    weight=float(row.get("weight", 1000.0)),
                    batch_number=str(row.get("batch_number", row.get("batch", "BP-B-2026"))).upper(),
                    source=str(row.get("source", "Winnowing Plant")),
                    warehouse_location=str(row.get("warehouse_location", "Shed 2")),
                    status="Available",
                    created_by=current_user.username
                )
                db.add(bp)
                imported_count += 1
        except Exception as e:
            logger.warning(f"Skipping row due to formatting issue: {e}")

    upload.status = "Imported"
    db.commit()

    return standard_response(
        data={"imported_count": imported_count, "target_module": target_module},
        message=f"Successfully imported {imported_count} verified records into {target_module}"
    )
