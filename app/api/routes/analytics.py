from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.database import get_db
from app.models.user import User
from app.models.performance import Recommendation
from app.schemas.analytics import DashboardResponse, ReadinessBreakdown, RecommendationsResponse, RecommendationItem
from app.api.deps import get_current_user
from app.services.analytics_service import get_dashboard_data, compute_readiness_score, generate_recommendations, _categorize_readiness
from app.models.resume import Resume

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_dashboard_data(current_user.id, db)
    return DashboardResponse(**data)


@router.get("/readiness", response_model=ReadinessBreakdown)
async def get_readiness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get resume score
    resume_r = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id, Resume.is_active == True)
        .order_by(Resume.created_at.desc()).limit(1)
    )
    resume = resume_r.scalar_one_or_none()
    resume_score = float(resume.overall_score) if resume else 0.0

    performance_score = current_user.avg_score or 0.0
    sessions_count = current_user.total_interviews or 0

    # Simple improvement rate: 0.1 baseline
    improvement_rate = 0.1

    final_score = compute_readiness_score(
        resume_score, performance_score, 0.7, improvement_rate, sessions_count
    )

    await db.execute(update(User).where(User.id == current_user.id).values(readiness_score=final_score))

    category = _categorize_readiness(final_score)

    milestones = {
        "Not Ready": "Complete 5 interviews and score above 60% to reach 'Improving'",
        "Improving": "Maintain 70%+ accuracy for 2 weeks to reach 'Interview Ready'",
        "Interview Ready": "You're ready! Apply to your target roles now.",
    }

    weights = {"resume": 0.30, "performance": 0.50, "consistency": 0.20}
    if sessions_count < 2:
        weights = {"resume": 0.60, "performance": 0.30, "consistency": 0.10}

    return ReadinessBreakdown(
        overall_score=final_score,
        category=category,
        resume_score=resume_score,
        performance_score=performance_score,
        consistency_score=0.7,
        improvement_rate=improvement_rate,
        component_weights=weights,
        next_milestone=milestones.get(category),
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recs_data = await generate_recommendations(current_user.id, db)
    items = [RecommendationItem(**r) for r in recs_data]

    urgent = [r for r in items if r.priority <= 3]
    suggested = [r for r in items if 4 <= r.priority <= 7]
    optional = [r for r in items if r.priority > 7]

    return RecommendationsResponse(
        urgent=urgent, suggested=suggested, optional=optional, total=len(items)
    )


@router.patch("/recommendations/{rec_id}/dismiss")
async def dismiss_recommendation(
    rec_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Recommendation).where(
            Recommendation.id == rec_id,
            Recommendation.user_id == current_user.id
        ).values(is_dismissed=True)
    )
    return {"message": "Recommendation dismissed"}
