import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func

from app.db.database import get_db
from app.models.user import User
from app.models.question import Question, InterviewSession, DifficultyLevel, QuestionCategory, SessionStatus
from app.models.performance import Attempt, PerformanceLog, AttemptResult
from app.schemas.interview import (
    InterviewStartRequest, InterviewStartResponse, QuestionResponse,
    AnswerSubmitRequest, AnswerSubmitResponse, AnswerFeedback, SessionSummaryResponse
)
from app.api.deps import get_current_user
from app.services.interview_engine import (
    compute_adaptive_difficulty, evaluate_answer_with_ai,
    generate_adaptive_question, detect_behavioral_signals, compute_session_behavioral_insights
)
from app.services.analytics_service import compute_readiness_score

router = APIRouter(prefix="/interview", tags=["Interview"])

QUESTION_BANK = {
    "data_structures": [
        {"text": "Explain the difference between a stack and a queue. When would you use each?", "difficulty": "easy", "expected_answer": "Stack is LIFO, queue is FIFO. Stacks used for undo operations, recursion call stack. Queues used for BFS, task scheduling, message queues.", "answer_keywords": ["LIFO", "FIFO", "stack", "queue", "recursion", "BFS"]},
        {"text": "What is a hash table? How does it handle collisions?", "difficulty": "medium", "expected_answer": "Hash table maps keys to values using a hash function. Collisions handled via chaining (linked list at each bucket) or open addressing (probing).", "answer_keywords": ["hash function", "collision", "chaining", "open addressing", "O(1)"]},
        {"text": "Explain Red-Black Trees and why they are self-balancing.", "difficulty": "hard", "expected_answer": "Red-Black tree is a BST with color properties ensuring O(log n) operations. Rules: root is black, no consecutive red nodes, equal black height on all paths.", "answer_keywords": ["BST", "balanced", "O(log n)", "rotation", "color", "black height"]},
    ],
    "algorithms": [
        {"text": "What is the time complexity of quicksort? When does it degrade to O(n²)?", "difficulty": "easy", "expected_answer": "Quicksort avg O(n log n), worst case O(n²) when pivot is always min/max. Randomized pivot or median-of-three avoids worst case.", "answer_keywords": ["O(n log n)", "O(n²)", "pivot", "partition", "average case"]},
        {"text": "Explain dynamic programming. Give an example.", "difficulty": "medium", "expected_answer": "DP solves problems by breaking into overlapping subproblems and storing results (memoization/tabulation). Example: Fibonacci, longest common subsequence, knapsack.", "answer_keywords": ["overlapping subproblems", "memoization", "tabulation", "optimal substructure", "Fibonacci"]},
        {"text": "Describe Dijkstra's algorithm and its time complexity.", "difficulty": "hard", "expected_answer": "Dijkstra finds shortest paths from source. Uses priority queue, relaxes edges. O((V+E) log V) with min-heap. Doesn't work with negative edges.", "answer_keywords": ["shortest path", "priority queue", "relaxation", "O((V+E)logV)", "negative weights"]},
    ],
    "databases": [
        {"text": "What is the difference between SQL and NoSQL databases?", "difficulty": "easy", "expected_answer": "SQL: relational, ACID, structured schema, vertical scaling. NoSQL: flexible schema, horizontal scaling, eventual consistency, various models (document, KV, graph).", "answer_keywords": ["ACID", "relational", "schema", "horizontal scaling", "eventual consistency"]},
        {"text": "Explain database indexing and its tradeoffs.", "difficulty": "medium", "expected_answer": "Indexes speed up reads via B-tree or hash structures but slow down writes and use storage. Choose indexes based on query patterns, cardinality, and write frequency.", "answer_keywords": ["B-tree", "index", "read performance", "write overhead", "cardinality"]},
        {"text": "What is database sharding? Explain horizontal vs vertical partitioning.", "difficulty": "hard", "expected_answer": "Sharding splits data across multiple DB instances by shard key. Horizontal: rows split across shards. Vertical: tables/columns split. Trade-off: complexity vs scalability.", "answer_keywords": ["shard key", "horizontal partitioning", "vertical partitioning", "distributed", "rebalancing"]},
    ],
    "system_design": [
        {"text": "How would you design a URL shortener like bit.ly?", "difficulty": "medium", "expected_answer": "Components: API server, hash generation (base62), DB (id→URL), cache (Redis). Handle redirects with HTTP 301/302. Scale with CDN, read replicas, distributed ID gen.", "answer_keywords": ["hash", "base62", "Redis", "CDN", "redirect", "distributed"]},
        {"text": "Design a rate limiter for an API.", "difficulty": "medium", "expected_answer": "Strategies: token bucket, leaky bucket, sliding window counter. Store counts in Redis with TTL. Return 429 when limit exceeded. Distribute across nodes with atomic ops.", "answer_keywords": ["token bucket", "sliding window", "Redis", "429", "atomic", "distributed"]},
        {"text": "How would you design a distributed message queue?", "difficulty": "hard", "expected_answer": "Topics/partitions for parallelism, producers write to partitions, consumers in groups for load balancing. Replication for fault tolerance. Offset tracking, at-least-once delivery, idempotent consumers.", "answer_keywords": ["partition", "consumer group", "replication", "offset", "idempotent", "fault tolerance"]},
    ],
    "behavioral": [
        {"text": "Tell me about a time you had to deal with a difficult technical problem. How did you approach it?", "difficulty": "easy", "expected_answer": "Look for STAR method: Situation, Task, Action, Result. Should show problem-solving process, collaboration, and learning.", "answer_keywords": ["situation", "challenge", "approach", "solution", "learned", "result"]},
        {"text": "Describe a time when you had a disagreement with a team member. How was it resolved?", "difficulty": "medium", "expected_answer": "Good answer shows empathy, communication, willingness to compromise, focus on team goals over personal views.", "answer_keywords": ["communication", "perspective", "compromise", "team", "resolution", "outcome"]},
    ],
    "python": [
        {"text": "What is the difference between a list and a tuple in Python?", "difficulty": "easy", "expected_answer": "Lists are mutable, tuples immutable. Tuples faster and hashable (usable as dict keys). Lists for dynamic data, tuples for fixed records.", "answer_keywords": ["mutable", "immutable", "hashable", "performance", "tuple", "list"]},
        {"text": "Explain Python's GIL and how it affects multithreading.", "difficulty": "hard", "expected_answer": "GIL is a mutex that prevents multiple threads from executing Python bytecode simultaneously. Limits CPU-bound parallelism. Use multiprocessing for CPU-bound, asyncio/threading for I/O-bound tasks.", "answer_keywords": ["GIL", "mutex", "CPU-bound", "I/O-bound", "multiprocessing", "asyncio"]},
    ],
}


def _build_question_response(q: Question, number: int, total: int) -> QuestionResponse:
    return QuestionResponse(
        id=q.id, text=q.text, category=q.category,
        difficulty=q.difficulty, question_type=q.question_type,
        avg_response_time=q.avg_response_time,
        question_number=number, total_questions=total,
    )


async def _get_or_create_questions(db: AsyncSession, target_role: str, difficulty: DifficultyLevel, exclude_ids: List[str], category: Optional[str] = None) -> Optional[Question]:
    """Get a question from DB, filtering by difficulty and excluding seen ones."""
    query = select(Question).where(Question.difficulty == difficulty)
    if category:
        query = query.where(Question.category == category)
    if exclude_ids:
        query = query.where(~Question.id.in_([uuid.UUID(i) for i in exclude_ids if i]))
    query = query.order_by(func.random()).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _seed_questions_if_empty(db: AsyncSession):
    """Seed question bank if empty."""
    result = await db.execute(select(func.count(Question.id)))
    count = result.scalar()
    if count and count > 0:
        return

    from app.models.question import QuestionType, QuestionCategory
    type_map = {"behavioral": QuestionType.behavioral, "system_design": QuestionType.system_design}
    cat_map = {k: getattr(QuestionCategory, k, QuestionCategory.problem_solving) for k in QUESTION_BANK}

    for cat_key, questions in QUESTION_BANK.items():
        for q_data in questions:
            q = Question(
                text=q_data["text"],
                category=cat_map.get(cat_key, QuestionCategory.problem_solving),
                difficulty=DifficultyLevel(q_data["difficulty"]),
                question_type=type_map.get(cat_key, QuestionType.technical),
                expected_answer=q_data["expected_answer"],
                answer_keywords=q_data["answer_keywords"],
                avg_response_time=120.0,
                role_relevance={"backend": 0.8, "frontend": 0.6, "sde": 0.9},
                is_ai_generated=False,
            )
            db.add(q)
    await db.flush()


@router.post("/start", response_model=InterviewStartResponse, status_code=201)
async def start_interview(
    payload: InterviewStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _seed_questions_if_empty(db)

    # Get first question
    first_q = await _get_or_create_questions(db, payload.target_role, payload.starting_difficulty, [])

    if not first_q:
        # Generate with AI
        q_data = await generate_adaptive_question(payload.target_role, "data_structures", payload.starting_difficulty.value, [], [])
        from app.models.question import QuestionType, QuestionCategory
        first_q = Question(
            text=q_data["text"], category=QuestionCategory.data_structures,
            difficulty=payload.starting_difficulty, question_type=QuestionType.technical,
            expected_answer=q_data["expected_answer"], answer_keywords=q_data["answer_keywords"],
            avg_response_time=q_data.get("avg_response_time", 120), is_ai_generated=True,
        )
        db.add(first_q)
        await db.flush()

    session = InterviewSession(
        user_id=current_user.id,
        target_role=payload.target_role,
        total_questions=payload.total_questions,
        starting_difficulty=payload.starting_difficulty,
        current_difficulty=payload.starting_difficulty,
        question_ids=[str(first_q.id)],
        current_question_index=0,
    )
    db.add(session)
    await db.flush()

    return InterviewStartResponse(
        session_id=session.id,
        first_question=_build_question_response(first_q, 1, payload.total_questions),
        message=f"Interview started! You have {payload.total_questions} questions. Good luck!",
    )


@router.post("/submit", response_model=AnswerSubmitResponse)
async def submit_answer(
    payload: AnswerSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load session
    sess_result = await db.execute(select(InterviewSession).where(
        and_(InterviewSession.id == payload.session_id, InterviewSession.user_id == current_user.id)
    ))
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.in_progress:
        raise HTTPException(status_code=400, detail="Session is not active")

    # Load question
    q_result = await db.execute(select(Question).where(Question.id == payload.question_id))
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Evaluate answer with AI
    eval_result = await evaluate_answer_with_ai(
        question.text,
        question.expected_answer or "",
        payload.answer,
        question.answer_keywords or [],
        question.category.value,
    )

    # Behavioral signals
    recent_attempts_r = await db.execute(
        select(Attempt.score, Attempt.time_taken).where(
            and_(Attempt.session_id == session.id)
        ).order_by(Attempt.created_at.desc()).limit(5)
    )
    recent_data = recent_attempts_r.fetchall()
    recent_scores = [r[0] for r in recent_data]
    recent_times = [r[1] for r in recent_data]

    signals = detect_behavioral_signals(
        payload.time_taken, question.avg_response_time or 120,
        eval_result["score"], recent_scores, recent_times
    )

    # Save attempt
    result_enum = AttemptResult(eval_result["result"])
    attempt = Attempt(
        session_id=session.id,
        question_id=question.id,
        user_id=current_user.id,
        user_answer=payload.answer,
        result=result_enum,
        score=eval_result["score"],
        time_taken=payload.time_taken,
        ai_feedback=eval_result["ai_feedback"],
        strengths=eval_result["strengths"],
        weaknesses=eval_result["weaknesses"],
        answer_length=len(payload.answer.split()),
        was_time_pressured=signals["was_time_pressured"],
        had_hesitation=signals["had_hesitation"],
    )
    db.add(attempt)
    await db.flush()

    # Adaptive difficulty
    new_difficulty, diff_change = compute_adaptive_difficulty(
        session.current_difficulty, recent_scores + [eval_result["score"]]
    )

    # Update session
    new_idx = session.current_question_index + 1
    session_complete = new_idx >= session.total_questions

    next_question_resp = None
    if not session_complete:
        # Get next question with adaptive difficulty
        exclude = list(session.question_ids or [])
        next_q = await _get_or_create_questions(db, session.target_role, new_difficulty, exclude)
        if not next_q:
            # AI-generate one
            q_data = await generate_adaptive_question(
                session.target_role, "algorithms", new_difficulty.value,
                [question.text], [r[0] for r in recent_data if r[0] < 50 and len(recent_data) > 0]
            )
            from app.models.question import QuestionType, QuestionCategory
            next_q = Question(
                text=q_data["text"], category=QuestionCategory.algorithms,
                difficulty=new_difficulty, question_type=QuestionType.technical,
                expected_answer=q_data["expected_answer"],
                answer_keywords=q_data.get("answer_keywords", []),
                avg_response_time=q_data.get("avg_response_time", 120),
                is_ai_generated=True,
            )
            db.add(next_q)
            await db.flush()

        updated_ids = list(session.question_ids or []) + [str(next_q.id)]
        await db.execute(update(InterviewSession).where(InterviewSession.id == session.id).values(
            current_question_index=new_idx,
            current_difficulty=new_difficulty,
            question_ids=updated_ids,
        ))
        next_question_resp = _build_question_response(next_q, new_idx + 1, session.total_questions)
    else:
        # Complete session
        all_attempts_r = await db.execute(
            select(Attempt).where(Attempt.session_id == session.id)
        )
        all_attempts = all_attempts_r.scalars().all()

        total_score = sum(a.score for a in all_attempts) / max(len(all_attempts), 1)
        correct = sum(1 for a in all_attempts if a.result == AttemptResult.correct)
        accuracy = (correct / max(len(all_attempts), 1)) * 100
        avg_time = sum(a.time_taken for a in all_attempts) / max(len(all_attempts), 1)

        behavioral = compute_session_behavioral_insights([{"score": a.score, "time_taken": a.time_taken} for a in all_attempts])

        await db.execute(update(InterviewSession).where(InterviewSession.id == session.id).values(
            status=SessionStatus.completed,
            current_question_index=new_idx,
            total_score=total_score,
            accuracy_percentage=accuracy,
            avg_response_time=avg_time,
            completed_at=datetime.utcnow(),
            panic_score=behavioral["panic_score"],
            consistency_score=behavioral["consistency_score"],
            time_pressure_impact=behavioral["time_pressure_impact"],
        ))

        # Update user stats
        user_sessions_r = await db.execute(
            select(func.count(InterviewSession.id), func.avg(InterviewSession.total_score)).where(
                and_(InterviewSession.user_id == current_user.id, InterviewSession.status == SessionStatus.completed)
            )
        )
        sess_stats = user_sessions_r.one()
        sessions_count = int(sess_stats[0] or 1)
        new_avg = float(sess_stats[1] or 0)

        readiness = compute_readiness_score(
            current_user.readiness_score, new_avg,
            behavioral["consistency_score"], 0.1, sessions_count
        )

        await db.execute(update(User).where(User.id == current_user.id).values(
            total_interviews=sessions_count,
            avg_score=round(new_avg, 1),
            readiness_score=readiness,
            last_active=datetime.utcnow(),
        ))

    feedback = AnswerFeedback(
        result=eval_result["result"],
        score=eval_result["score"],
        ai_feedback=eval_result["ai_feedback"],
        strengths=eval_result["strengths"],
        weaknesses=eval_result["weaknesses"],
        expected_keywords=eval_result["expected_keywords"],
    )

    return AnswerSubmitResponse(
        attempt_id=attempt.id,
        feedback=feedback,
        next_question=next_question_resp,
        session_complete=session_complete,
        difficulty_changed=diff_change,
    )


@router.get("/session/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sess_r = await db.execute(select(InterviewSession).where(
        and_(InterviewSession.id == uuid.UUID(session_id), InterviewSession.user_id == current_user.id)
    ))
    session = sess_r.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    attempts_r = await db.execute(
        select(Attempt, Question).join(Question, Attempt.question_id == Question.id)
        .where(Attempt.session_id == session.id)
    )
    rows = attempts_r.fetchall()

    topic_breakdown = {}
    correct = partial = incorrect = 0
    for attempt, question in rows:
        cat = question.category.value
        if cat not in topic_breakdown:
            topic_breakdown[cat] = {"score": 0, "attempts": 0, "correct": 0}
        topic_breakdown[cat]["score"] += attempt.score
        topic_breakdown[cat]["attempts"] += 1
        if attempt.result == AttemptResult.correct:
            correct += 1
            topic_breakdown[cat]["correct"] += 1
        elif attempt.result == AttemptResult.partial:
            partial += 1
        else:
            incorrect += 1

    for cat in topic_breakdown:
        d = topic_breakdown[cat]
        d["avg_score"] = round(d["score"] / max(d["attempts"], 1), 1)
        d["accuracy"] = round(d["correct"] / max(d["attempts"], 1) * 100, 1)

    strongest = max(topic_breakdown, key=lambda c: topic_breakdown[c]["accuracy"]) if topic_breakdown else None
    weakest = min(topic_breakdown, key=lambda c: topic_breakdown[c]["accuracy"]) if topic_breakdown else None

    duration = 0.0
    if session.completed_at and session.started_at:
        duration = (session.completed_at - session.started_at).seconds / 60

    behavioral_insights = []
    if session.panic_score and session.panic_score > 0.4:
        behavioral_insights.append("Panic detected — rapid wrong answers under pressure.")
    if session.consistency_score and session.consistency_score < 0.5:
        behavioral_insights.append("Inconsistent performance across topics.")
    if not behavioral_insights:
        behavioral_insights.append("Solid performance throughout the session!")

    return SessionSummaryResponse(
        session_id=session.id,
        target_role=session.target_role,
        status=session.status,
        total_questions=session.total_questions,
        correct_count=correct,
        incorrect_count=incorrect,
        partial_count=partial,
        total_score=session.total_score or 0,
        accuracy_percentage=session.accuracy_percentage or 0,
        avg_response_time=session.avg_response_time or 0,
        duration_minutes=round(duration, 1),
        panic_score=session.panic_score or 0,
        consistency_score=session.consistency_score or 0,
        topic_breakdown=topic_breakdown,
        strongest_topic=strongest,
        weakest_topic=weakest,
        behavioral_insights=behavioral_insights,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


@router.get("/history")
async def get_interview_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.started_at.desc()).limit(limit)
    )
    sessions = result.scalars().all()
    return [{
        "session_id": s.id,
        "target_role": s.target_role,
        "status": s.status,
        "total_score": s.total_score,
        "accuracy": s.accuracy_percentage,
        "questions": s.total_questions,
        "started_at": s.started_at,
    } for s in sessions]
