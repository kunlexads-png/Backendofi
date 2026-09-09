import uuid
import enum
from datetime import datetime, date
from sqlalchemy import Column, String, Float, Date, DateTime, Text, Enum as SQLEnum
from app.database import Base


class TransactionType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    DISPOSAL = "DISPOSAL"


class StockModule(str, enum.Enum):
    ARRIVAL = "ARRIVAL"
    FINISHED_GOODS = "FINISHED_GOODS"
    BYPRODUCT = "BYPRODUCT"


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    product = Column(String(100), index=True, nullable=False)
    module = Column(SQLEnum(StockModule), index=True, nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), index=True, nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    weight = Column(Float, nullable=False)  # in KG or MT
    batch = Column(String(50), index=True, nullable=False)
    reference_number = Column(String(100), index=True, nullable=False)
    previous_balance = Column(Float, nullable=False)
    new_balance = Column(Float, nullable=False)
    user = Column(String(100), nullable=False)
    date = Column(Date, default=date.today, index=True, nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<StockMovement {self.transaction_id} {self.transaction_type} {self.product}: {self.weight}kg>"
