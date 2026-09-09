import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Float, Date, DateTime, Text
from app.database import Base

BYPRODUCT_PRODUCTS = [
    "Cluster",
    "Cluster Beans",
    "Dust",
    "Nibs",
    "Shaft",
    "FM",
    "Disposed Material"
]


class Byproduct(Base):
    __tablename__ = "byproducts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String(50), unique=True, index=True, nullable=False)
    date = Column(Date, default=date.today, index=True, nullable=False)
    product = Column(String(50), index=True, nullable=False)  # Cluster, Cluster Beans, Dust, Nibs, Shaft, FM, Disposed Material
    quantity = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)  # in KG
    batch_number = Column(String(50), index=True, nullable=False)
    source = Column(String(100), nullable=False)  # e.g. Cleaning Plant, Winnowing, Pressing
    sap_batch = Column(String(50), index=True, nullable=True)
    customer = Column(String(150), index=True, nullable=True)
    warehouse_location = Column(String(100), nullable=False)
    status = Column(String(50), default="Available", index=True, nullable=False)  # Available, Disposed, In-Process, Transferred
    remarks = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Byproduct {self.record_id} - {self.product} - {self.weight}kg>"
