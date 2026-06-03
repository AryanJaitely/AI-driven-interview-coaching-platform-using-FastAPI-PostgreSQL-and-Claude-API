from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class ResumeStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    analyzed = "analyzed"
    failed = "failed"


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(500), nullable=False)
    file_url = Column(Text)
    file_size = Column(Integer)
    status = Column(SAEnum(ResumeStatus), default=ResumeStatus.pending)

    raw_text = Column(Text)
    parsed_data = Column(JSON)

    overall_score = Column(Float, default=0.0)
    ats_score = Column(Float, default=0.0)
    skills_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    format_score = Column(Float, default=0.0)

    extracted_skills = Column(ARRAY(String))
    extracted_keywords = Column(ARRAY(String))
    missing_skills = Column(ARRAY(String))
    suggestions = Column(JSON)

    detected_role = Column(String(100))
    role_match_score = Column(Float)
    years_experience = Column(Float)
    education_level = Column(String(100))
    projects_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="resumes")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100))
    aliases = Column(ARRAY(String))
    is_popular = Column(Boolean, default=False)
    demand_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
