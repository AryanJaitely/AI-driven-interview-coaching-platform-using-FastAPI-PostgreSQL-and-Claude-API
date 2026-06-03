import json
import re
from typing import Dict, List, Any, Optional, Tuple
import openai
from app.core.config import settings
from app.models.question import DifficultyLevel

client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Adaptive difficulty thresholds
DIFFICULTY_UP_THRESHOLD = 0.70    # >70% accuracy → increase difficulty
DIFFICULTY_DOWN_THRESHOLD = 0.40  # <40% accuracy → decrease difficulty
WINDOW_SIZE = 3                    # Rolling window of attempts to evaluate


def compute_adaptive_difficulty(
    current_difficulty: DifficultyLevel,
    recent_scores: List[float],
) -> Tuple[DifficultyLevel, Optional[str]]:
    if len(recent_scores) < WINDOW_SIZE:
        return current_difficulty, None

    avg = sum(recent_scores[-WINDOW_SIZE:]) / WINDOW_SIZE
    order = [DifficultyLevel.easy, DifficultyLevel.medium, DifficultyLevel.hard]
    idx = order.index(current_difficulty)

    if avg >= DIFFICULTY_UP_THRESHOLD * 100 and idx < 2:
        return order[idx + 1], "increased"
    elif avg < DIFFICULTY_DOWN_THRESHOLD * 100 and idx > 0:
        return order[idx - 1], "decreased"
    return current_difficulty, None


async def evaluate_answer_with_ai(
    question_text: str,
    expected_answer: str,
    user_answer: str,
    answer_keywords: List[str],
    category: str,
) -> Dict[str, Any]:
    prompt = f"""You are an expert technical interviewer. Evaluate the candidate's answer.

Question: {question_text}
Category: {category}
Expected Answer Summary: {expected_answer or 'Not provided'}
Key Concepts Expected: {', '.join(answer_keywords or [])}

Candidate's Answer: {user_answer}

Evaluate and return ONLY valid JSON (no markdown):
{{
  "result": "correct" | "partial" | "incorrect",
  "score": 0-100,
  "ai_feedback": "2-3 sentence constructive feedback",
  "strengths": ["list of what they did well"],
  "weaknesses": ["list of gaps or mistakes"],
  "expected_keywords": ["key concepts from expected answer"]
}}

Scoring guide:
- correct (80-100): Covers main concepts accurately with good depth
- partial (40-79): Some correct points but missing key aspects
- incorrect (0-39): Fundamentally wrong or completely missing the point
"""
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r"```json\n?|\n?```", "", text).strip()
        return json.loads(text)
    except Exception:
        # Fallback basic evaluation
        answer_lower = user_answer.lower()
        matched = sum(1 for kw in (answer_keywords or []) if kw.lower() in answer_lower)
        total = max(len(answer_keywords or []), 1)
        ratio = matched / total
        if ratio >= 0.7:
            result, score = "correct", 75
        elif ratio >= 0.3:
            result, score = "partial", 50
        else:
            result, score = "incorrect", 20
        return {
            "result": result, "score": score,
            "ai_feedback": "Answer evaluated based on keyword matching.",
            "strengths": [f"Mentioned {matched} key concepts"],
            "weaknesses": ["Could not perform detailed AI evaluation"],
            "expected_keywords": answer_keywords or [],
        }


async def generate_adaptive_question(
    target_role: str,
    category: str,
    difficulty: str,
    previous_questions: List[str],
    weak_areas: List[str],
) -> Dict[str, Any]:
    prev_context = "\n".join(f"- {q}" for q in previous_questions[-3:]) if previous_questions else "None"
    weak_context = ", ".join(weak_areas) if weak_areas else "none identified"

    prompt = f"""Generate a unique interview question for a {target_role} candidate.

Category: {category}
Difficulty: {difficulty}
Candidate's weak areas: {weak_context}
Recently asked questions (do NOT repeat):
{prev_context}

Return ONLY valid JSON:
{{
  "text": "The interview question",
  "expected_answer": "A comprehensive model answer (3-5 sentences)",
  "answer_keywords": ["key", "concepts", "list"],
  "avg_response_time": 120,
  "scoring_rubric": {{"depth": 40, "accuracy": 40, "clarity": 20}}
}}"""
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=500,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r"```json\n?|\n?```", "", text).strip()
        return json.loads(text)
    except Exception:
        return {
            "text": f"Explain a key concept in {category} relevant to {target_role} development.",
            "expected_answer": "Candidate should demonstrate understanding of core concepts.",
            "answer_keywords": [category, target_role],
            "avg_response_time": 120,
            "scoring_rubric": {"depth": 40, "accuracy": 40, "clarity": 20},
        }


def detect_behavioral_signals(
    time_taken: float,
    expected_time: float,
    score: float,
    recent_scores: List[float],
    recent_times: List[float],
) -> Dict[str, Any]:
    signals = {
        "was_time_pressured": False,
        "had_hesitation": False,
        "panic_score": 0.0,
    }

    # Time pressure: answered in <30% of expected time with low score
    if expected_time and time_taken < expected_time * 0.3 and score < 50:
        signals["was_time_pressured"] = True

    # Hesitation: took >2x expected time
    if expected_time and time_taken > expected_time * 2:
        signals["had_hesitation"] = True

    # Panic detection: rapid wrong answers (short time + low score pattern)
    if len(recent_scores) >= 3 and len(recent_times) >= 3:
        recent_avg_score = sum(recent_scores[-3:]) / 3
        recent_avg_time = sum(recent_times[-3:]) / 3
        if recent_avg_score < 40 and recent_avg_time < 30:
            signals["panic_score"] = 0.8
        elif recent_avg_score < 50:
            signals["panic_score"] = 0.4

    return signals


def compute_session_behavioral_insights(
    attempts_data: List[Dict],
) -> Dict[str, Any]:
    if not attempts_data:
        return {"panic_score": 0.0, "consistency_score": 1.0, "time_pressure_impact": 0.0, "insights": []}

    scores = [a["score"] for a in attempts_data]
    times = [a["time_taken"] for a in attempts_data]
    insights = []

    # Consistency: std deviation of scores
    if len(scores) > 1:
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        consistency_score = max(0.0, 1.0 - (std_dev / 50))
    else:
        consistency_score = 1.0

    # Panic: many wrong answers in short time
    panic_events = sum(1 for a in attempts_data if a["score"] < 30 and a["time_taken"] < 20)
    panic_score = min(panic_events / max(len(attempts_data), 1), 1.0)

    # Time-pressure impact: correlation between time and score
    time_pressure_pairs = [(t, s) for t, s in zip(times, scores) if t < 30]
    if len(time_pressure_pairs) > 2:
        fast_avg = sum(s for _, s in time_pressure_pairs) / len(time_pressure_pairs)
        overall_avg = sum(scores) / len(scores)
        time_pressure_impact = max(0.0, (overall_avg - fast_avg) / max(overall_avg, 1))
    else:
        time_pressure_impact = 0.0

    if panic_score > 0.5:
        insights.append("You show signs of panic during the interview — rapid incorrect answers detected.")
    if consistency_score < 0.5:
        insights.append("Your performance is inconsistent. Focus on stabilizing your fundamentals.")
    if time_pressure_impact > 0.3:
        insights.append("You perform significantly worse under time pressure. Practice timed problems.")
    if not insights:
        insights.append("Solid and consistent performance throughout the session!")

    return {
        "panic_score": round(panic_score, 3),
        "consistency_score": round(consistency_score, 3),
        "time_pressure_impact": round(time_pressure_impact, 3),
        "insights": insights,
    }
