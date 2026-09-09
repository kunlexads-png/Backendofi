from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.arrival import router as arrival_router
from app.routes.finished_goods import router as finished_goods_router
from app.routes.byproduct import router as byproduct_router
from app.routes.stock import router as stock_router
from app.routes.uploads import router as uploads_router
from app.routes.dashboard import router as dashboard_router
from app.routes.ai_assistant import router as ai_assistant_router
from app.routes.reports import router as reports_router

__all__ = [
    "auth_router",
    "users_router",
    "arrival_router",
    "finished_goods_router",
    "byproduct_router",
    "stock_router",
    "uploads_router",
    "dashboard_router",
    "ai_assistant_router",
    "reports_router",
]
