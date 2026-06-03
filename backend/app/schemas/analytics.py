from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class TopicPerformance(BaseModel):
    topic: str
    accuracy: float
    total_attempts: int
    avg_score: float
    trend: str


class WeeklyTrend(BaseModel):
    week_start: str
    sessions: int
    avg_score: float
    accuracy: float
    questions_attempted: int


class DashboardResponse(BaseModel):
    total_sessions: int
    total_questions_attempted: int
    overall_accuracy: float
    avg_session_score: float
    current_streak: int
    readiness_score: float
    readiness_category: str
    topic_performance: List[TopicPerformance]
    strongest_topics: List[str]
    weakest_topics: List[str]
    weekly_trends: List[WeeklyTrend]
    score_over_time: List[Dict[str, Any]]
    accuracy_over_time: List[Dict[str, Any]]
    avg_response_time: float
    panic_frequency: float
    consistency_score: float
    behavioral_insights: List[str]
    last_session_date: Optional[datetime]
    sessions_this_week: int
    sessions_this_month: int


class ReadinessBreakdown(BaseModel):
    overall_score: float
    category: str
    resume_score: float
    performance_score: float
    consistency_score: float
    improvement_rate: float
    component_weights: Dict[str, float]
    next_milestone: Optional[str]


class RecommendationItem(BaseModel):
    id: str
    type: str
    priority: int
    title: str
    description: str
    action_url: Optional[str]
    based_on: Dict[str, Any]


class RecommendationsResponse(BaseModel):
    urgent: List[RecommendationItem]
    suggested: List[RecommendationItem]
    optional: List[RecommendationItem]
    total: int
