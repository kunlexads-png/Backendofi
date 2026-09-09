import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_path = Column(String(500), nullable=False)
    status = Column(String(50), default="Uploaded", nullable=False)  # Uploaded, Processing, Parsed, Imported, Error
    extracted_data = Column(Text, nullable=True)  # JSON string of extracted rows or summary
    error_message = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UploadedFile {self.original_filename} ({self.file_type}) - {self.status}>"
