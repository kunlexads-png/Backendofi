import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_supervisor
from app.services.report_service import ReportService
from app.utils.helpers import standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Warehouse Reports & Exports"])


@router.get("/{report_type}", summary="Generate warehouse report with optional file export")
def get_report(
    report_type: str,
    format: Optional[str] = Query("json", description="Export format: json, csv, excel, or pdf"),
    period: Optional[str] = Query("daily", description="For arrival reports: daily, weekly, or monthly"),
    current_user: User = Depends(require_supervisor),
    db: Session = Depends(get_db)
):
    """
    Generates structured reports for:
    - arrivals (daily, weekly, monthly)
    - finished_goods
    - byproducts
    - stock_movements
    - disposals
    
    Supports formats: json, csv, excel, pdf.
    """
    report_type_clean = report_type.lower().replace("-", "_")

    if report_type_clean in ("arrival", "arrivals"):
        data = ReportService.get_arrival_report(db, period=period)
        title = f"{period.capitalize()} Cocoa Arrival Report"
    elif report_type_clean in ("finished_goods", "finishedgoods"):
        data = ReportService.get_finished_goods_report(db)
        title = "Finished Goods Inventory Report"
    elif report_type_clean in ("byproduct", "byproducts"):
        data = ReportService.get_byproducts_report(db)
        title = "By-Product Warehouse Report"
    elif report_type_clean in ("stock_movement", "stock_movements", "movements"):
        data = ReportService.get_stock_movements_report(db)
        title = "Centralized Stock Movements Ledger"
    elif report_type_clean in ("disposal", "disposals"):
        data = ReportService.get_disposals_report(db)
        title = "Material Disposal Audit Report"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown report type '{report_type}'. Supported: arrivals, finished_goods, byproducts, stock_movements, disposals"
        )

    # Format dispatch
    fmt = format.lower()
    if fmt == "csv":
        csv_text = ReportService.export_csv(data)
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={report_type_clean}_report.csv"}
        )
    elif fmt in ("excel", "xlsx"):
        excel_bytes = ReportService.export_excel(data, sheet_name=report_type_clean)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={report_type_clean}_report.xlsx"}
        )
    elif fmt == "pdf":
        pdf_bytes = ReportService.export_simple_pdf(title, data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_type_clean}_report.pdf"}
        )

    # Default JSON
    return standard_response(
        data={
            "report_title": title,
            "period": period if "arrival" in report_type_clean else None,
            "records_count": len(data),
            "records": data
        },
        message=f"{title} generated successfully"
    )
