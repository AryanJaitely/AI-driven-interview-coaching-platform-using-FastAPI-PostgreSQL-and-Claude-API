from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.question import DifficultyLevel, QuestionCategory, QuestionType, SessionStatus


class InterviewStartRequest(BaseModel):
    target_role: str
    total_questions: int = 10
    categories: Optional[List[str]] = None
    starting_difficulty: DifficultyLevel = DifficultyLevel.easy


class QuestionResponse(BaseModel):
    id: UUID
    text: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    question_type: QuestionType
    avg_response_time: Optional[float]
    question_number: int
    total_questions: int

    class Config:
        from_attributes = True


class InterviewStartResponse(BaseModel):
    session_id: UUID
    first_question: QuestionResponse
    message: str


class AnswerSubmitRequest(BaseModel):
    session_id: UUID
    question_id: UUID
    answer: str
    time_taken: float


class AnswerFeedback(BaseModel):
    result: str
    score: float
    ai_feedback: str
    strengths: List[str]
    weaknesses: List[str]
    expected_keywords: List[str]


class AnswerSubmitResponse(BaseModel):
    attempt_id: UUID
    feedback: AnswerFeedback
    next_question: Optional[QuestionResponse]
    session_complete: bool
    difficulty_changed: Optional[str]


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    target_role: str
    status: SessionStatus
    total_questions: int
    correct_count: int
    incorrect_count: int
    partial_count: int
    total_score: float
    accuracy_percentage: float
    avg_response_time: float
    duration_minutes: float
    panic_score: float
    consistency_score: float
    topic_breakdown: Dict[str, Any]
    strongest_topic: Optional[str]
    weakest_topic: Optional[str]
    behavioral_insights: List[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
