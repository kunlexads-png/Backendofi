import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.ai_service import AIService
from app.utils.helpers import standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Warehouse Assistant"])


class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000, description="Warehouse inquiry")


@router.post("/ask", summary="Ask the OFI Cocoa Warehouse AI Assistant")
def ask_ai(
    payload: AskQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Interrogates the warehouse database to answer natural language operational inquiries.
    Factual numbers are always verified against PostgreSQL prior to response generation.
    Enforces strict topic boundary controls and prevents SQL injection.
    """
    logger.info(f"AI question by {current_user.username}: {payload.question}")
    
    result = AIService.ask(payload.question, db)
    return standard_response(
        data=result,
        message="AI response generated successfully"
    )
