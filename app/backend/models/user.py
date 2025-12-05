"""
User models
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    role: UserRole = UserRole.USER
    firebase_uid: str
    microsoft_id: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation model"""
    email: EmailStr
    firebase_uid: str
    role: UserRole = UserRole.USER
    microsoft_id: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None


class UserUpdate(BaseModel):
    """User update model"""
    role: Optional[UserRole] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
