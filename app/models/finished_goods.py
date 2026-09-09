import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Text
from app.database import Base


class FinishedGoods(Base):
    __tablename__ = "finished_goods"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String(50), unique=True, index=True, nullable=False)
    date = Column(Date, default=date.today, index=True, nullable=False)
    product = Column(String(100), index=True, nullable=False)  # e.g. Cocoa Butter, Cocoa Liquor, Cocoa Powder, Cocoa Cake
    product_type = Column(String(100), nullable=False)  # e.g. Natural, Alkalized
    batch_number = Column(String(50), index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    number_of_bags = Column(Integer, default=0, nullable=False)
    weight = Column(Float, nullable=False)  # in MT or KG
    warehouse_location = Column(String(100), nullable=False)
    customer = Column(String(150), index=True, nullable=True)
    production_date = Column(Date, nullable=True)
    status = Column(String(50), default="In Stock", index=True, nullable=False)  # In Stock, Dispatched, Reserved
    sap_batch = Column(String(50), index=True, nullable=True)
    storage_location = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<FinishedGoods {self.record_id} - {self.product} - {self.weight}kg>"
