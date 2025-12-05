"""
Chat models
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Citation(BaseModel):
    """Citation model"""
    source: str
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    snippet: str
    page_number: Optional[int] = None


class RetrievalContext(BaseModel):
    """Retrieval context from Vertex AI RAG"""
    content: str
    source: str
    score: float
    chunk_id: Optional[str] = None


class Message(BaseModel):
    """Message model"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    citations: list[Citation] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    citations: list[Citation] = Field(default_factory=list)
    retrieval_contexts: list[RetrievalContext] = Field(default_factory=list)
    conversation_id: str
