from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class DifficultyLevel(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionType(str, enum.Enum):
    technical = "technical"
    behavioral = "behavioral"
    coding = "coding"
    system_design = "system_design"


class QuestionCategory(str, enum.Enum):
    data_structures = "data_structures"
    algorithms = "algorithms"
    databases = "databases"
    system_design = "system_design"
    networking = "networking"
    os_concepts = "os_concepts"
    python = "python"
    javascript = "javascript"
    java = "java"
    react = "react"
    nodejs = "nodejs"
    machine_learning = "machine_learning"
    behavioral = "behavioral"
    problem_solving = "problem_solving"


class SessionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    text = Column(Text, nullable=False)
    category = Column(SAEnum(QuestionCategory), nullable=False, index=True)
    difficulty = Column(SAEnum(DifficultyLevel), nullable=False, index=True)
    question_type = Column(SAEnum(QuestionType), nullable=False)
    expected_answer = Column(Text)
    answer_keywords = Column(ARRAY(String))
    scoring_rubric = Column(JSON)
    tags = Column(ARRAY(String))
    role_relevance = Column(JSON)
    avg_response_time = Column(Float)
    times_used = Column(Integer, default=0)
    avg_score = Column(Float, default=0.0)
    is_ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempts = relationship("Attempt", back_populates="question")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)

    target_role = Column(String(100), nullable=False)
    status = Column(SAEnum(SessionStatus), default=SessionStatus.in_progress)
    total_questions = Column(Integer, default=10)
    current_question_index = Column(Integer, default=0)
    starting_difficulty = Column(SAEnum(DifficultyLevel), default=DifficultyLevel.easy)
    current_difficulty = Column(SAEnum(DifficultyLevel), default=DifficultyLevel.easy)

    total_score = Column(Float)
    accuracy_percentage = Column(Float)
    avg_response_time = Column(Float)
    panic_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    time_pressure_impact = Column(Float, default=0.0)
    question_ids = Column(ARRAY(String))

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="interview_sessions")
    attempts = relationship("Attempt", back_populates="session", cascade="all, delete-orphan")
