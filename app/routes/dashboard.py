from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.arrival import Arrival, ArrivalStatus
from app.models.finished_goods import FinishedGoods
from app.models.byproduct import Byproduct, BYPRODUCT_PRODUCTS
from app.models.stock_movement import StockMovement, TransactionType, StockModule
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.stock_service import StockService
from app.utils.helpers import get_date_bounds, standard_response

router = APIRouter(prefix="/dashboard", tags=["Warehouse Dashboard"])


@router.get("/summary", summary="Complete dashboard executive summary metrics")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today, start_of_week, start_of_month = get_date_bounds()

    # Arrivals KPIs
    total_arrivals = db.query(Arrival).count()
    completed_arrivals = db.query(Arrival).filter(Arrival.status == ArrivalStatus.COMPLETED).count()
    pending_offloading = db.query(Arrival).filter(
        Arrival.status.in_([ArrivalStatus.PENDING, ArrivalStatus.ARRIVED, ArrivalStatus.WAITING_FOR_OFFLOADING])
    ).count()

    total_cocoa_received_kg = db.query(func.coalesce(func.sum(Arrival.net_weight), 0.0)).filter(
        Arrival.status == ArrivalStatus.COMPLETED
    ).scalar()

    today_arrivals_count = db.query(Arrival).filter(Arrival.date == today).count()
    today_cocoa_kg = db.query(func.coalesce(func.sum(Arrival.net_weight), 0.0)).filter(
        Arrival.date == today
    ).scalar()

    weekly_arrivals_count = db.query(Arrival).filter(Arrival.date >= start_of_week).count()
    monthly_arrivals_count = db.query(Arrival).filter(Arrival.date >= start_of_month).count()

    # Stock metrics
    stock_summary = StockService.get_stock_summary(db)
    byproducts_map = stock_summary.get("byproducts_breakdown", {})

    # Disposed quantity this month
    disposed_this_month = db.query(func.coalesce(func.sum(StockMovement.weight), 0.0)).filter(
        StockMovement.transaction_type == TransactionType.DISPOSAL,
        StockMovement.date >= start_of_month
    ).scalar()

    return standard_response(
        data={
            "total_cocoa_received_kg": round(float(total_cocoa_received_kg), 2),
            "total_arrivals": total_arrivals,
            "completed_arrivals": completed_arrivals,
            "pending_offloading": pending_offloading,
            "today_arrivals": today_arrivals_count,
            "today_cocoa_kg": round(float(today_cocoa_kg), 2),
            "weekly_arrivals": weekly_arrivals_count,
            "monthly_arrivals": monthly_arrivals_count,
            "total_finished_goods_stock_kg": stock_summary.get("total_finished_goods_stock", 0.0),
            "total_byproduct_stock_kg": stock_summary.get("total_byproduct_stock", 0.0),
            "dust_stock_kg": byproducts_map.get("Dust", 0.0),
            "nibs_stock_kg": byproducts_map.get("Nibs", 0.0),
            "cluster_stock_kg": byproducts_map.get("Cluster", 0.0),
            "shaft_stock_kg": byproducts_map.get("Shaft", 0.0),
            "fm_stock_kg": byproducts_map.get("FM", 0.0),
            "disposed_quantity_kg": round(float(disposed_this_month), 2),
            "as_of": str(today)
        },
        message="Dashboard executive summary retrieved"
    )


@router.get("/arrivals", summary="Arrivals trend and distribution data for charts")
def get_dashboard_arrivals(
    days: int = Query(7, ge=1, le=30, description="Past number of days to plot"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # Daily trend
    daily_records = db.query(
        Arrival.date,
        func.count(Arrival.id).label("trucks_count"),
        func.coalesce(func.sum(Arrival.number_of_bags), 0).label("bags_count"),
        func.coalesce(func.sum(Arrival.net_weight), 0.0).label("net_weight_kg")
    ).filter(
        Arrival.date >= start_date
    ).group_by(Arrival.date).order_by(Arrival.date.asc()).all()

    # Status distribution
    status_distribution = db.query(
        Arrival.status,
        func.count(Arrival.id)
    ).group_by(Arrival.status).all()

    # Supplier distribution
    top_suppliers = db.query(
        Arrival.supplier,
        func.count(Arrival.id).label("count"),
        func.coalesce(func.sum(Arrival.net_weight), 0.0).label("weight")
    ).group_by(Arrival.supplier).order_by(func.sum(Arrival.net_weight).desc()).limit(5).all()

    return standard_response(
        data={
            "daily_trend": [
                {
                    "date": str(r.date),
                    "trucks": r.trucks_count,
                    "bags": r.bags_count,
                    "net_weight": round(float(r.net_weight_kg), 2)
                }
                for r in daily_records
            ],
            "status_distribution": {
                (s.value if hasattr(s, "value") else str(s)): c for s, c in status_distribution
            },
            "top_suppliers": [
                {"supplier": s, "count": c, "weight": round(float(w), 2)}
                for s, c, w in top_suppliers
            ]
        },
        message="Arrival dashboard statistics retrieved"
    )


@router.get("/stock", summary="Detailed stock distribution across all warehouses")
def get_dashboard_stock(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = StockService.get_stock_summary(db)
    return standard_response(
        data=summary,
        message="Stock levels retrieved"
    )


@router.get("/byproducts", summary="By-product stock breakdown and distribution")
def get_dashboard_byproducts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    balances = {}
    for p in BYPRODUCT_PRODUCTS:
        balances[p] = StockService.get_current_product_balance(db, p, StockModule.BYPRODUCT)

    recent_disposals = db.query(StockMovement).filter(
        StockMovement.module == StockModule.BYPRODUCT,
        StockMovement.transaction_type == TransactionType.DISPOSAL
    ).order_by(StockMovement.created_at.desc()).limit(5).all()

    return standard_response(
        data={
            "products": balances,
            "total_byproduct_kg": sum(balances.values()),
            "recent_disposals": [
                {
                    "product": d.product,
                    "weight": d.weight,
                    "date": str(d.date),
                    "reason": d.remarks
                }
                for d in recent_disposals
            ]
        },
        message="By-product warehouse metrics retrieved"
    )


@router.get("/recent-activity", summary="Recent warehouse stock transactions and arrivals")
def get_dashboard_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recent_movements = db.query(StockMovement).order_by(
        StockMovement.created_at.desc()
    ).limit(limit).all()

    recent_arrivals = db.query(Arrival).order_by(
        Arrival.created_at.desc()
    ).limit(limit).all()

    return standard_response(
        data={
            "movements": [
                {
                    "transaction_id": m.transaction_id,
                    "product": m.product,
                    "type": m.transaction_type.value if hasattr(m.transaction_type, "value") else str(m.transaction_type),
                    "weight": m.weight,
                    "user": m.user,
                    "date": str(m.date),
                    "remarks": m.remarks
                }
                for m in recent_movements
            ],
            "arrivals": [
                {
                    "arrival_id": a.arrival_id,
                    "truck_number": a.truck_number,
                    "supplier": a.supplier,
                    "net_weight": a.net_weight,
                    "bags": a.number_of_bags,
                    "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                    "time": a.time,
                    "date": str(a.date)
                }
                for a in recent_arrivals
            ]
        },
        message="Recent activity retrieved"
    )
