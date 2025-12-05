"""
Agent models
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status"""
    ACTIVE = "active"
    INDEXING = "indexing"
    ERROR = "error"
    ARCHIVED = "archived"


class AgentSettings(BaseModel):
    """Agent settings"""
    model: str = Field(default="gemini-1.5-pro", description="Vertex AI model name")
    temperature: float = Field(default=0.7, ge=0, le=2)
    system_prompt: str = Field(default="")
    max_tokens: int = Field(default=4096, ge=100, le=32000)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0, le=1)
    include_citations: bool = Field(default=True)
    streaming: bool = Field(default=True)


class Agent(BaseModel):
    """Agent model"""
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    bucket_name: str
    corpus_id: Optional[str] = None
    data_store_id: Optional[str] = None
    status: AgentStatus = AgentStatus.ACTIVE
    settings: AgentSettings = Field(default_factory=AgentSettings)
    document_count: int = 0

    class Config:
        from_attributes = True


class AgentCreate(BaseModel):
    """Agent creation model"""
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500)


class AgentUpdate(BaseModel):
    """Agent update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    settings: Optional[AgentSettings] = None
    status: Optional[AgentStatus] = None
