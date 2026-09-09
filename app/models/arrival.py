import uuid
import enum
from datetime import datetime, date
from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Text, Enum as SQLEnum
from app.database import Base


class ArrivalStatus(str, enum.Enum):
    PENDING = "Pending"
    ARRIVED = "Arrived"
    WAITING_FOR_OFFLOADING = "Waiting for Offloading"
    OFFLOADING = "Offloading"
    COMPLETED = "Completed"
    REJECTED = "Rejected"


class Arrival(Base):
    __tablename__ = "arrivals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    arrival_id = Column(String(50), unique=True, index=True, nullable=False)
    date = Column(Date, default=date.today, index=True, nullable=False)
    time = Column(String(10), nullable=False)  # HH:MM format
    truck_number = Column(String(50), index=True, nullable=False)
    driver_name = Column(String(100), nullable=False)
    supplier = Column(String(150), index=True, nullable=False)
    customer = Column(String(150), index=True, nullable=True)
    product = Column(String(100), default="Cocoa Beans", nullable=False)
    number_of_bags = Column(Integer, nullable=False)
    gross_weight = Column(Float, nullable=False)
    tare_weight = Column(Float, nullable=False)
    net_weight = Column(Float, nullable=False)
    batch_number = Column(String(50), index=True, nullable=False)
    warehouse = Column(String(100), nullable=False)
    cluster = Column(String(100), nullable=False)
    moisture = Column(Float, nullable=False)
    status = Column(SQLEnum(ArrivalStatus), default=ArrivalStatus.PENDING, index=True, nullable=False)
    offloading_status = Column(String(50), default="Not Started", nullable=False)
    remarks = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Arrival {self.arrival_id} - {self.truck_number} - {self.status}>"
