from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole, ExperienceLevel
import re


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: Optional[ExperienceLevel] = ExperienceLevel.fresher

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("Username must be 3-30 chars, alphanumeric + underscore only")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    target_role: Optional[str] = None
    experience_level: Optional[ExperienceLevel] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: UserRole
    target_role: Optional[str]
    experience_level: ExperienceLevel
    bio: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    total_interviews: int
    avg_score: float
    readiness_score: float
    streak_days: int
    created_at: datetime

    class Config:
        from_attributes = True
