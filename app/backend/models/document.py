"""
Document models
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class Document(BaseModel):
    """Document model"""
    id: str
    agent_id: str
    file_name: str
    original_name: str
    gcs_path: str
    content_type: str
    size: int
    uploaded_by: str
    uploaded_at: datetime
    status: DocumentStatus = DocumentStatus.UPLOADED
    error_message: Optional[str] = None
    chunks_count: int = 0

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    """Document creation model"""
    original_name: str
    content_type: str
    size: int
