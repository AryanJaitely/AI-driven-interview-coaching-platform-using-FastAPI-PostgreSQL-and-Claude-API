from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class UserRole(str, enum.Enum):
    candidate = "candidate"
    admin = "admin"


class ExperienceLevel(str, enum.Enum):
    fresher = "fresher"
    junior = "junior"
    mid = "mid"
    senior = "senior"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    avatar_url = Column(Text)
    role = Column(SAEnum(UserRole), default=UserRole.candidate)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    target_role = Column(String(100))
    experience_level = Column(SAEnum(ExperienceLevel), default=ExperienceLevel.fresher)
    bio = Column(Text)
    linkedin_url = Column(String(500))
    github_url = Column(String(500))

    total_interviews = Column(Integer, default=0)
    avg_score = Column(Float, default=0.0)
    readiness_score = Column(Float, default=0.0)
    streak_days = Column(Integer, default=0)
    last_active = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    performance_logs = relationship("PerformanceLog", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
