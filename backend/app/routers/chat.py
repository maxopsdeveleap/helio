"""
Chat API router for SQL-RAG queries.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.sql_rag import SQLRAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize SQL-RAG service
sql_rag = SQLRAGService()


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str
    sql: Optional[str] = None
    row_count: int
    results: List[Dict[str, Any]]
    trace: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Answer a natural language question about candidates and positions.

    Args:
        request: Chat request with question

    Returns:
        Chat response with answer, SQL, and trace
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info(f"Received chat question: {request.question}")

    try:
        result = sql_rag.ask(request.question)
        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def get_examples():
    """
    Get example questions users can ask.

    Returns:
        List of example questions
    """
    examples = [
        {
            "category": "Candidates",
            "questions": [
                "List all candidates with Python skills",
                "How many candidates are in the database?",
                "Show me candidates with Kubernetes experience",
                "Which candidates have the most skills?"
            ]
        },
        {
            "category": "Positions",
            "questions": [
                "How many open positions are there?",
                "List positions by company",
                "Which positions have no candidates?",
                "Show me all remote positions"
            ]
        },
        {
            "category": "Analytics",
            "questions": [
                "Count candidates by location",
                "Which skills are most common among candidates?",
                "Show positions with urgent priority"
            ]
        }
    ]
    return {"examples": examples}
