import os
import uuid
import json
import csv
import io
import logging
from typing import Dict, Any, List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.utils.validators import validate_file_extension, validate_file_size

logger = logging.getLogger(__name__)


class FileService:
    @staticmethod
    def ensure_upload_dir() -> str:
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir

    @staticmethod
    async def save_uploaded_file(
        db: Session,
        file: UploadFile,
        user: User
    ) -> UploadedFile:
        """
        Validates, saves the file to disk securely, and creates an UploadedFile record.
        """
        filename = file.filename or "unknown_file"
        ext = validate_file_extension(filename)
        
        # Read content to check size
        content = await file.read()
        validate_file_size(len(content))
        
        upload_dir = FileService.ensure_upload_dir()
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        db_file = UploadedFile(
            filename=unique_filename,
            original_filename=filename,
            file_type=ext,
            file_size=len(content),
            file_path=file_path,
            status="Uploaded",
            created_by=user.username
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # Parse extracted data asynchronously or synchronously
        try:
            extraction_result = FileService.extract_file_content(file_path, ext, content)
            db_file.extracted_data = json.dumps(extraction_result)
            db_file.status = "Parsed"
            db.commit()
            db.refresh(db_file)
        except Exception as e:
            logger.error(f"Error parsing file {filename}: {e}")
            db_file.status = "Error"
            db_file.error_message = str(e)
            db.commit()

        return db_file

    @staticmethod
    def extract_file_content(file_path: str, ext: str, content: bytes) -> Dict[str, Any]:
        """
        Extracts tabular or text data from spreadsheets, CSVs, and PDFs.
        """
        if ext == "csv":
            return FileService._parse_csv(content)
        elif ext in ("xlsx", "xls"):
            return FileService._parse_excel(file_path)
        elif ext == "pdf":
            return FileService._parse_pdf(file_path, content)
        elif ext in ("jpg", "jpeg", "png"):
            return {
                "file_type": "image",
                "preview_note": "Image file received and stored securely.",
                "valid_rows": [],
                "invalid_rows": [],
                "total_rows": 0
            }
        return {"raw_text": "Unsupported for automated data extraction"}

    @staticmethod
    def _parse_csv(content: bytes) -> Dict[str, Any]:
        try:
            text = content.decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            headers = reader.fieldnames or []
            
            valid_rows = []
            invalid_rows = []
            row_num = 1

            for row in reader:
                row_num += 1
                # Check minimum required data for warehouse rows (e.g. product or weight or date)
                if not any(row.values()):
                    continue
                
                # Simple validation checks
                errors = []
                if "weight" in row:
                    try:
                        float(row["weight"])
                    except (ValueError, TypeError):
                        errors.append("Invalid weight value")
                if "quantity" in row:
                    try:
                        float(row["quantity"])
                    except (ValueError, TypeError):
                        errors.append("Invalid quantity value")
                        
                if errors:
                    invalid_rows.append({"row_number": row_num, "data": row, "errors": errors})
                else:
                    valid_rows.append({"row_number": row_num, "data": row})

            return {
                "file_type": "csv",
                "headers": list(headers),
                "total_rows": len(valid_rows) + len(invalid_rows),
                "valid_count": len(valid_rows),
                "invalid_count": len(invalid_rows),
                "valid_rows": valid_rows[:100],  # preview top 100
                "invalid_rows": invalid_rows
            }
        except Exception as e:
            return {"error": f"Failed to parse CSV: {str(e)}"}

    @staticmethod
    def _parse_excel(file_path: str) -> Dict[str, Any]:
        try:
            import pandas as pd
            df = pd.read_excel(file_path, engine="openpyxl")
            # Replace NaNs
            df = df.where(pd.notnull(df), None)
            headers = [str(c) for c in df.columns]
            
            valid_rows = []
            invalid_rows = []
            for idx, row in df.iterrows():
                row_dict = {str(k): (v if v is not None else "") for k, v in row.to_dict().items()}
                valid_rows.append({"row_number": idx + 2, "data": row_dict})

            return {
                "file_type": "excel",
                "headers": headers,
                "total_rows": len(valid_rows),
                "valid_count": len(valid_rows),
                "invalid_count": 0,
                "valid_rows": valid_rows[:100],
                "invalid_rows": []
            }
        except ImportError:
            # Fallback if pandas/openpyxl not installed
            return {
                "file_type": "excel",
                "headers": [],
                "note": "Spreadsheet saved. Install pandas and openpyxl for deep in-memory inspection."
            }
        except Exception as e:
            return {"error": f"Failed to read Excel file: {str(e)}"}

    @staticmethod
    def _parse_pdf(file_path: str, content: bytes) -> Dict[str, Any]:
        extracted_text = ""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                extracted_text += page.get_text() + "\n"
        except ImportError:
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(content))
                for page in reader.pages:
                    extracted_text += (page.extract_text() or "") + "\n"
            except Exception:
                extracted_text = "PDF stored successfully. Install PyMuPDF (fitz) or pypdf for deep text extraction."

        return {
            "file_type": "pdf",
            "extracted_text": extracted_text[:2000],  # preview 2000 chars
            "char_count": len(extracted_text),
            "requires_review": True
        }
