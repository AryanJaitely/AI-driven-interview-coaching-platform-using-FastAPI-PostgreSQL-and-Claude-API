import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.database import get_db
from app.models.user import User
from app.models.resume import Resume, ResumeStatus
from app.schemas.resume import ResumeAnalysisResponse, ResumeUploadResponse
from app.api.deps import get_current_user
from app.services import resume_parser

router = APIRouter(prefix="/resume", tags=["Resume"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def process_resume(resume_id: str, file_path: str, user_target_role: str, db_url: str):
    """Background task to process uploaded resume."""
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Resume).where(Resume.id == resume_id))
            resume = result.scalar_one_or_none()
            if not resume:
                return

            await db.execute(update(Resume).where(Resume.id == resume_id).values(status=ResumeStatus.processing))
            await db.commit()

            raw_text = resume_parser.extract_text_from_pdf(file_path)
            parsed_data = await resume_parser.parse_resume_with_ai(raw_text)

            skills = parsed_data.get("skills", [])
            keywords = parsed_data.get("keywords", [])
            detected_role, role_match = resume_parser.detect_role(skills, keywords)
            target = user_target_role or detected_role
            missing_skills = resume_parser.compute_missing_skills(skills, target)
            scores = resume_parser.compute_scores(parsed_data, raw_text)
            suggestions = resume_parser.generate_suggestions(parsed_data, scores, missing_skills)
            years_exp = sum(e.get("years", 0) for e in parsed_data.get("experience", []))
            edu = parsed_data.get("education", [])
            edu_level = edu[0].get("degree", "Unknown") if edu else "Unknown"
            projects_count = len(parsed_data.get("projects", []))

            await db.execute(update(Resume).where(Resume.id == resume_id).values(
                status=ResumeStatus.analyzed,
                raw_text=raw_text[:50000],
                parsed_data=parsed_data,
                overall_score=scores["overall_score"],
                ats_score=scores["ats_score"],
                skills_score=scores["skills_score"],
                experience_score=scores["experience_score"],
                format_score=scores["format_score"],
                extracted_skills=skills[:50],
                extracted_keywords=keywords[:50],
                missing_skills=missing_skills[:20],
                suggestions=suggestions,
                detected_role=detected_role,
                role_match_score=role_match,
                years_experience=years_exp,
                education_level=edu_level,
                projects_count=projects_count,
            ))
            await db.commit()
        except Exception as e:
            await db.execute(update(Resume).where(Resume.id == resume_id).values(status=ResumeStatus.failed))
            await db.commit()
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ["application/pdf"]:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    # Save temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(content)
    tmp.close()

    # Deactivate old resumes
    await db.execute(
        update(Resume).where(Resume.user_id == current_user.id).values(is_active=False)
    )

    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename,
        file_size=len(content),
        status=ResumeStatus.pending,
        is_active=True,
    )
    db.add(resume)
    await db.flush()

    background_tasks.add_task(
        process_resume,
        str(resume.id),
        tmp.name,
        current_user.target_role or "",
        "",
    )

    return ResumeUploadResponse(
        resume_id=resume.id,
        message="Resume uploaded successfully. Analysis in progress.",
        status=ResumeStatus.pending,
    )


@router.get("/analysis", response_model=ResumeAnalysisResponse)
async def get_resume_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id, Resume.is_active == True)
        .order_by(Resume.created_at.desc()).limit(1)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload your resume.")
    return resume


@router.get("/history")
async def get_resume_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc()).limit(10)
    )
    resumes = result.scalars().all()
    return [{"id": r.id, "filename": r.original_filename, "score": r.overall_score, "status": r.status, "created_at": r.created_at} for r in resumes]
