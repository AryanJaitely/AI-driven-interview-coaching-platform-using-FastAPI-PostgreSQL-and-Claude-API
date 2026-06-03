from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base


class AttemptResult(str, enum.Enum):
    correct = "correct"
    partial = "partial"
    incorrect = "incorrect"
    skipped = "skipped"


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    user_answer = Column(Text)
    result = Column(SAEnum(AttemptResult), nullable=False)
    score = Column(Float, default=0.0)
    time_taken = Column(Float, nullable=False)
    started_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    ai_feedback = Column(Text)
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    model_score_breakdown = Column(JSON)

    was_time_pressured = Column(Boolean, default=False)
    had_hesitation = Column(Boolean, default=False)
    answer_length = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")


class PerformanceLog(Base):
    __tablename__ = "performance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=True)

    log_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    topic_scores = Column(JSON)
    topic_attempts = Column(JSON)
    overall_score = Column(Float)
    accuracy = Column(Float)
    avg_response_time = Column(Float)
    questions_attempted = Column(Integer)
    correct_count = Column(Integer)
    incorrect_count = Column(Integer)
    partial_count = Column(Integer)
    readiness_score = Column(Float)
    panic_events = Column(Integer, default=0)
    consistency_index = Column(Float, default=0.0)

    user = relationship("User", back_populates="performance_logs")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    type = Column(String(50))
    priority = Column(Integer, default=5)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    action_url = Column(Text)
    based_on = Column(JSON)
    is_dismissed = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")
