from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from datetime import datetime, timedelta
from uuid import UUID

from app.models.performance import Attempt, PerformanceLog, Recommendation
from app.models.question import InterviewSession, Question, SessionStatus
from app.models.user import User


async def get_dashboard_data(user_id: UUID, db: AsyncSession) -> Dict[str, Any]:
    # Total sessions
    sessions_result = await db.execute(
        select(func.count(InterviewSession.id)).where(
            and_(InterviewSession.user_id == user_id, InterviewSession.status == SessionStatus.completed)
        )
    )
    total_sessions = sessions_result.scalar() or 0

    # Total questions attempted
    attempts_result = await db.execute(
        select(func.count(Attempt.id)).where(Attempt.user_id == user_id)
    )
    total_questions = attempts_result.scalar() or 0

    # Overall accuracy
    correct_result = await db.execute(
        select(func.count(Attempt.id)).where(
            and_(Attempt.user_id == user_id, Attempt.result == "correct")
        )
    )
    correct_count = correct_result.scalar() or 0
    overall_accuracy = (correct_count / max(total_questions, 1)) * 100

    # Avg session score
    avg_score_result = await db.execute(
        select(func.avg(InterviewSession.total_score)).where(
            and_(InterviewSession.user_id == user_id, InterviewSession.status == SessionStatus.completed)
        )
    )
    avg_session_score = float(avg_score_result.scalar() or 0)

    # Topic performance via GROUP BY
    topic_result = await db.execute(
        text("""
            SELECT q.category,
                   COUNT(a.id) as total_attempts,
                   AVG(a.score) as avg_score,
                   SUM(CASE WHEN a.result = 'correct' THEN 1 ELSE 0 END)::float / COUNT(a.id) * 100 as accuracy
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            WHERE a.user_id = :user_id
            GROUP BY q.category
            ORDER BY accuracy DESC
        """),
        {"user_id": str(user_id)}
    )
    topic_rows = topic_result.fetchall()

    topic_performance = []
    for row in topic_rows:
        topic_performance.append({
            "topic": row[0],
            "total_attempts": row[1],
            "avg_score": round(float(row[2] or 0), 1),
            "accuracy": round(float(row[3] or 0), 1),
            "trend": "stable",
        })

    strongest = [t["topic"] for t in topic_performance[:2]] if topic_performance else []
    weakest = [t["topic"] for t in reversed(topic_performance[-2:])] if topic_performance else []

    # Weekly trends
    weekly_result = await db.execute(
        text("""
            SELECT
                DATE_TRUNC('week', s.started_at) as week_start,
                COUNT(s.id) as sessions,
                AVG(s.total_score) as avg_score,
                AVG(s.accuracy_percentage) as accuracy,
                SUM(COALESCE(array_length(s.question_ids, 1), 0)) as questions
            FROM interview_sessions s
            WHERE s.user_id = :user_id AND s.status = 'completed'
            GROUP BY DATE_TRUNC('week', s.started_at)
            ORDER BY week_start DESC
            LIMIT 12
        """),
        {"user_id": str(user_id)}
    )
    weekly_rows = weekly_result.fetchall()
    weekly_trends = [
        {
            "week_start": str(row[0])[:10] if row[0] else "",
            "sessions": int(row[1] or 0),
            "avg_score": round(float(row[2] or 0), 1),
            "accuracy": round(float(row[3] or 0), 1),
            "questions_attempted": int(row[4] or 0),
        }
        for row in weekly_rows
    ]

    # Score over time (last 30 sessions)
    score_time_result = await db.execute(
        select(InterviewSession.started_at, InterviewSession.total_score, InterviewSession.accuracy_percentage)
        .where(and_(InterviewSession.user_id == user_id, InterviewSession.status == SessionStatus.completed))
        .order_by(InterviewSession.started_at.desc())
        .limit(30)
    )
    score_time_rows = score_time_result.fetchall()
    score_over_time = [{"date": str(r[0])[:10], "score": round(float(r[1] or 0), 1)} for r in reversed(score_time_rows)]
    accuracy_over_time = [{"date": str(r[0])[:10], "accuracy": round(float(r[2] or 0), 1)} for r in reversed(score_time_rows)]

    # Behavioral aggregates
    behavioral_result = await db.execute(
        select(
            func.avg(InterviewSession.panic_score),
            func.avg(InterviewSession.consistency_score),
            func.avg(InterviewSession.avg_response_time),
        ).where(and_(InterviewSession.user_id == user_id, InterviewSession.status == SessionStatus.completed))
    )
    b_row = behavioral_result.one()
    panic_freq = float(b_row[0] or 0)
    consistency = float(b_row[1] or 0)
    avg_response_time = float(b_row[2] or 0)

    behavioral_insights = []
    if panic_freq > 0.4:
        behavioral_insights.append("High panic frequency detected — work on staying calm under pressure.")
    if consistency < 0.5:
        behavioral_insights.append("Inconsistent performance — solidify your fundamentals.")
    if avg_response_time < 20:
        behavioral_insights.append("Very fast responses — ensure you're taking time to think through answers.")
    if not behavioral_insights:
        behavioral_insights.append("Strong behavioral patterns — keep up the good work!")

    # Readiness score from user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    readiness_score = float(user.readiness_score if user else 0)
    readiness_category = _categorize_readiness(readiness_score)

    # This week / this month
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    week_sessions_r = await db.execute(
        select(func.count(InterviewSession.id)).where(
            and_(InterviewSession.user_id == user_id, InterviewSession.started_at >= week_ago)
        )
    )
    month_sessions_r = await db.execute(
        select(func.count(InterviewSession.id)).where(
            and_(InterviewSession.user_id == user_id, InterviewSession.started_at >= month_ago)
        )
    )

    last_session_r = await db.execute(
        select(InterviewSession.started_at).where(
            and_(InterviewSession.user_id == user_id, InterviewSession.status == SessionStatus.completed)
        ).order_by(InterviewSession.started_at.desc()).limit(1)
    )
    last_session_date = last_session_r.scalar()

    return {
        "total_sessions": total_sessions,
        "total_questions_attempted": total_questions,
        "overall_accuracy": round(overall_accuracy, 1),
        "avg_session_score": round(avg_session_score, 1),
        "current_streak": user.streak_days if user else 0,
        "readiness_score": readiness_score,
        "readiness_category": readiness_category,
        "topic_performance": topic_performance,
        "strongest_topics": strongest,
        "weakest_topics": weakest,
        "weekly_trends": weekly_trends,
        "score_over_time": score_over_time,
        "accuracy_over_time": accuracy_over_time,
        "avg_response_time": round(avg_response_time, 1),
        "panic_frequency": round(panic_freq, 3),
        "consistency_score": round(consistency, 3),
        "behavioral_insights": behavioral_insights,
        "last_session_date": last_session_date,
        "sessions_this_week": week_sessions_r.scalar() or 0,
        "sessions_this_month": month_sessions_r.scalar() or 0,
    }


def _categorize_readiness(score: float) -> str:
    if score >= 75:
        return "Interview Ready"
    elif score >= 45:
        return "Improving"
    else:
        return "Not Ready"


def compute_readiness_score(
    resume_score: float,
    avg_performance_score: float,
    consistency_score: float,
    improvement_rate: float,
    sessions_count: int,
) -> float:
    # Weighted formula
    if sessions_count < 2:
        performance_weight = 0.30
        consistency_weight = 0.10
        resume_weight = 0.60
    else:
        performance_weight = 0.50
        consistency_weight = 0.20
        resume_weight = 0.30

    base = (
        resume_score * resume_weight +
        avg_performance_score * performance_weight +
        consistency_score * 100 * consistency_weight
    )
    # Bonus for improvement trend
    bonus = min(improvement_rate * 10, 10)
    return round(min(base + bonus, 100), 1)


async def generate_recommendations(user_id: UUID, db: AsyncSession) -> List[Dict]:
    recs = []

    # Get weak topics
    topic_result = await db.execute(
        text("""
            SELECT q.category,
                   AVG(a.score) as avg_score,
                   COUNT(a.id) as attempts
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            WHERE a.user_id = :user_id
            GROUP BY q.category
            HAVING AVG(a.score) < 60
            ORDER BY avg_score ASC
            LIMIT 5
        """),
        {"user_id": str(user_id)}
    )
    weak_topics = topic_result.fetchall()

    for i, row in enumerate(weak_topics):
        topic, avg_score, attempts = row
        recs.append({
            "id": f"rec_topic_{i}",
            "type": "topic",
            "priority": i + 1,
            "title": f"Improve your {topic.replace('_', ' ').title()} skills",
            "description": f"Your average score in {topic.replace('_', ' ')} is {round(float(avg_score), 1)}% across {attempts} attempts. Focus here to boost your readiness score.",
            "action_url": f"/practice?category={topic}",
            "based_on": {"category": topic, "avg_score": float(avg_score), "attempts": int(attempts)},
        })

    # Check if resume uploaded
    from app.models.resume import Resume
    resume_result = await db.execute(
        select(Resume).where(and_(Resume.user_id == user_id, Resume.is_active == True))
        .order_by(Resume.created_at.desc()).limit(1)
    )
    resume = resume_result.scalar_one_or_none()
    if not resume:
        recs.append({
            "id": "rec_resume_upload",
            "type": "resume",
            "priority": 1,
            "title": "Upload your resume for personalized questions",
            "description": "Uploading your resume enables the AI to tailor interview questions to your specific experience and skills.",
            "action_url": "/resume/upload",
            "based_on": {"reason": "no_resume"},
        })
    elif resume.overall_score < 60:
        recs.append({
            "id": "rec_resume_improve",
            "type": "resume",
            "priority": 2,
            "title": "Improve your resume score",
            "description": f"Your resume scored {resume.overall_score}/100. Implement the suggestions to improve ATS compatibility.",
            "action_url": "/resume/analysis",
            "based_on": {"score": resume.overall_score},
        })

    # Consistency recommendation
    sessions_result = await db.execute(
        select(func.count(InterviewSession.id)).where(
            and_(InterviewSession.user_id == user_id,
                 InterviewSession.started_at >= datetime.utcnow() - timedelta(days=7))
        )
    )
    week_sessions = sessions_result.scalar() or 0
    if week_sessions < 3:
        recs.append({
            "id": "rec_consistency",
            "type": "behavioral",
            "priority": 3,
            "title": "Practice more consistently",
            "description": f"You've done {week_sessions} session(s) this week. Aim for 5+ sessions/week for steady improvement.",
            "action_url": "/interview/start",
            "based_on": {"sessions_this_week": week_sessions},
        })

    return recs
