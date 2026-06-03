from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.resume import ResumeStatus


class ResumeSuggestion(BaseModel):
    category: str
    severity: str
    message: str
    action: str


class ResumeAnalysisResponse(BaseModel):
    id: UUID
    user_id: UUID
    original_filename: str
    status: ResumeStatus
    overall_score: float
    ats_score: float
    skills_score: float
    experience_score: float
    format_score: float
    extracted_skills: Optional[List[str]] = []
    extracted_keywords: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []
    suggestions: Optional[List[Dict]] = []
    detected_role: Optional[str]
    role_match_score: Optional[float]
    years_experience: Optional[float]
    education_level: Optional[str]
    projects_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    resume_id: UUID
    message: str
    status: ResumeStatus
