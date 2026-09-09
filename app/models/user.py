import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    WAREHOUSE_MANAGER = "Warehouse Manager"
    SUPERVISOR = "Supervisor"
    WAREHOUSE_OFFICER = "Warehouse Officer"
    VIEWER = "Viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.username} - {self.role}>"
