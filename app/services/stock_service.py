from datetime import date
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.stock_movement import StockMovement, TransactionType, StockModule
from app.models.user import User, UserRole
from app.utils.helpers import generate_unique_id


class StockService:
    @staticmethod
    def get_current_product_balance(
        db: Session,
        product: str,
        module: Optional[StockModule] = None
    ) -> float:
        """
        Retrieves the latest closing stock balance for a specific product.
        If no movements exist, returns 0.0.
        """
        query = db.query(StockMovement).filter(StockMovement.product == product)
        if module:
            query = query.filter(StockMovement.module == module)
        
        last_movement = query.order_by(StockMovement.created_at.desc()).first()
        return round(last_movement.new_balance, 2) if last_movement else 0.0

    @staticmethod
    def record_movement(
        db: Session,
        product: str,
        module: StockModule,
        transaction_type: TransactionType,
        weight: float,
        quantity: float,
        batch: str,
        reference_number: str,
        user: User,
        txn_date: Optional[date] = None,
        remarks: Optional[str] = None,
        allow_negative: bool = False
    ) -> StockMovement:
        """
        Records a stock movement, updating the balance according to:
        Opening Stock + Stock IN - Stock OUT - Disposal +/- Adjustments = Closing Stock.
        Enforces that stock cannot become negative unless explicitly allowed by an Admin.
        """
        if weight <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transaction weight must be positive"
            )

        previous_balance = StockService.get_current_product_balance(db, product, module)

        if transaction_type == TransactionType.IN:
            new_balance = previous_balance + weight
        elif transaction_type in (TransactionType.OUT, TransactionType.DISPOSAL):
            new_balance = previous_balance - weight
        elif transaction_type == TransactionType.TRANSFER:
            new_balance = previous_balance - weight
        elif transaction_type == TransactionType.ADJUSTMENT:
            new_balance = previous_balance + weight  # weight can be positive or negative for adjustment
        else:
            new_balance = previous_balance

        # Negative balance check
        if new_balance < 0:
            if not allow_negative or user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{product}'. Current balance: {previous_balance}kg, requested reduction: {weight}kg. Negative balance requires Admin authorization."
                )

        movement = StockMovement(
            transaction_id=generate_unique_id("TXN"),
            product=product,
            module=module,
            transaction_type=transaction_type,
            quantity=quantity,
            weight=weight,
            batch=batch,
            reference_number=reference_number,
            previous_balance=round(previous_balance, 2),
            new_balance=round(new_balance, 2),
            user=user.username,
            date=txn_date or date.today(),
            remarks=remarks
        )

        db.add(movement)
        db.flush()
        return movement

    @staticmethod
    def get_stock_summary(db: Session) -> Dict[str, Any]:
        """
        Calculates aggregate stock balances across Cocoa arrivals, Finished goods, and By-products.
        """
        from app.models.byproduct import BYPRODUCT_PRODUCTS
        
        # Calculate latest balance for all distinct products
        distinct_products = db.query(StockMovement.product, StockMovement.module).distinct().all()
        
        cocoa_stock = 0.0
        finished_goods_stock = 0.0
        byproduct_stock = 0.0
        byproducts_breakdown = {p: 0.0 for p in BYPRODUCT_PRODUCTS}
        balances_list = []

        for prod_name, mod in distinct_products:
            bal = StockService.get_current_product_balance(db, prod_name, mod)
            
            # Aggregate calculations (IN, OUT, DISPOSAL, ADJUSTMENT)
            totals = db.query(
                StockMovement.transaction_type,
                func.coalesce(func.sum(StockMovement.weight), 0.0)
            ).filter(
                StockMovement.product == prod_name,
                StockMovement.module == mod
            ).group_by(StockMovement.transaction_type).all()
            
            type_weights = {t: w for t, w in totals}
            stock_in = float(type_weights.get(TransactionType.IN, 0.0))
            stock_out = float(type_weights.get(TransactionType.OUT, 0.0)) + float(type_weights.get(TransactionType.TRANSFER, 0.0))
            disposal = float(type_weights.get(TransactionType.DISPOSAL, 0.0))
            adjustments = float(type_weights.get(TransactionType.ADJUSTMENT, 0.0))

            balances_list.append({
                "product": prod_name,
                "module": mod.value if hasattr(mod, "value") else str(mod),
                "opening_stock": 0.0,
                "stock_in": round(stock_in, 2),
                "stock_out": round(stock_out, 2),
                "disposal": round(disposal, 2),
                "adjustments": round(adjustments, 2),
                "closing_stock": round(bal, 2),
                "unit": "KG"
            })

            if mod == StockModule.ARRIVAL or "Cocoa" in prod_name:
                cocoa_stock += bal
            elif mod == StockModule.FINISHED_GOODS:
                finished_goods_stock += bal
            elif mod == StockModule.BYPRODUCT:
                byproduct_stock += bal
                if prod_name in byproducts_breakdown:
                    byproducts_breakdown[prod_name] = round(bal, 2)

        return {
            "total_cocoa_stock": round(cocoa_stock, 2),
            "total_finished_goods_stock": round(finished_goods_stock, 2),
            "total_byproduct_stock": round(byproduct_stock, 2),
            "byproducts_breakdown": byproducts_breakdown,
            "balances": balances_list
        }
