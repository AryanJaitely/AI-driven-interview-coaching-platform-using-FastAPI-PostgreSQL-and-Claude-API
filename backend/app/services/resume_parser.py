import json
import re
from typing import Dict, List, Any, Tuple
import pdfplumber
import openai
from app.core.config import settings

client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

ROLE_SKILL_MAP = {
    "backend": ["python", "java", "golang", "node.js", "postgresql", "redis", "docker", "kubernetes", "rest api", "microservices", "sql"],
    "frontend": ["react", "vue", "angular", "javascript", "typescript", "html", "css", "tailwind", "webpack", "graphql"],
    "fullstack": ["react", "node.js", "postgresql", "docker", "javascript", "typescript", "rest api", "git"],
    "data_scientist": ["python", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "sql", "jupyter", "statistics"],
    "devops": ["docker", "kubernetes", "jenkins", "aws", "terraform", "ansible", "ci/cd", "linux", "bash"],
    "sde": ["data structures", "algorithms", "system design", "python", "java", "git", "sql", "problem solving"],
}

IMPORTANT_KEYWORDS = [
    "rest api", "microservices", "agile", "scrum", "ci/cd", "tdd", "system design",
    "scalable", "distributed systems", "cloud", "aws", "gcp", "azure", "docker",
    "kubernetes", "machine learning", "deep learning", "data pipeline"
]


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            pt = page.extract_text()
            if pt:
                text += pt + "\n"
    return text.strip()


async def parse_resume_with_ai(raw_text: str) -> Dict[str, Any]:
    prompt = f"""You are an expert resume parser. Extract structured information from this resume.
Return ONLY valid JSON, no markdown, no explanation.

Resume:
---
{raw_text[:4000]}
---

Return this exact JSON structure:
{{
  "name": null, "email": null, "phone": null, "linkedin": null, "github": null,
  "summary": null,
  "skills": [],
  "experience": [{{"company":"","role":"","duration":"","years":0.0,"description":"","technologies":[]}}],
  "education": [{{"institution":"","degree":"","field":"","year":""}}],
  "projects": [{{"name":"","description":"","technologies":[],"url":null}}],
  "certifications": [],
  "keywords": []
}}"""

    try:
        if not client:
            raise Exception("No OpenAI key configured")
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )
        result_text = response.choices[0].message.content.strip()
        result_text = re.sub(r"```json\n?|\n?```", "", result_text).strip()
        return json.loads(result_text)
    except Exception:
        # Fallback: basic regex extraction
        skills = re.findall(r'\b(Python|Java|JavaScript|React|Node\.js|SQL|Docker|AWS|Git|TypeScript|Go|Golang|Flask|Django|FastAPI|MongoDB|PostgreSQL|Redis|Kubernetes)\b', raw_text, re.IGNORECASE)
        return {"skills": list(set([s.lower() for s in skills])), "experience": [], "education": [], "projects": [], "certifications": [], "keywords": []}


def detect_role(skills: List[str], keywords: List[str]) -> Tuple[str, float]:
    all_terms = [s.lower() for s in skills + keywords]
    scores = {}
    for role, role_skills in ROLE_SKILL_MAP.items():
        matches = sum(1 for s in role_skills if any(s in term for term in all_terms))
        scores[role] = matches / max(len(role_skills), 1)
    best_role = max(scores, key=scores.get)
    return best_role, round(scores[best_role] * 100, 1)


def compute_missing_skills(extracted_skills: List[str], target_role: str) -> List[str]:
    role_key = target_role.lower().replace(" ", "_").replace("-", "_")
    role_mapping = {
        "backend_engineer": "backend", "backend_developer": "backend",
        "frontend_engineer": "frontend", "frontend_developer": "frontend",
        "full_stack": "fullstack", "data_scientist": "data_scientist",
        "software_engineer": "sde", "sde": "sde", "devops_engineer": "devops",
    }
    mapped_role = role_mapping.get(role_key, "sde")
    required = ROLE_SKILL_MAP.get(mapped_role, ROLE_SKILL_MAP["sde"])
    extracted_lower = [s.lower() for s in extracted_skills]
    return [s for s in required if not any(s in e for e in extracted_lower)]


def compute_scores(parsed_data: Dict, raw_text: str) -> Dict[str, float]:
    skills = parsed_data.get("skills", [])
    experience = parsed_data.get("experience", [])
    projects = parsed_data.get("projects", [])
    education = parsed_data.get("education", [])

    skills_score = min(len(skills) * 5, 100)
    total_years = sum(e.get("years", 0) for e in experience)
    experience_score = min(total_years * 15, 100) if experience else min(len(projects) * 10, 60)

    format_checks = [
        bool(parsed_data.get("email")), bool(parsed_data.get("phone")),
        bool(parsed_data.get("summary")), bool(parsed_data.get("linkedin")),
        bool(parsed_data.get("github")), len(skills) > 3,
        bool(education), bool(projects or experience),
    ]
    format_score = sum(format_checks) / len(format_checks) * 100

    keywords_found = sum(1 for kw in IMPORTANT_KEYWORDS if kw in raw_text.lower())
    ats_score = min(keywords_found * 8, 100)

    overall = skills_score * 0.30 + experience_score * 0.30 + format_score * 0.20 + ats_score * 0.20
    return {
        "overall_score": round(overall, 1),
        "skills_score": round(skills_score, 1),
        "experience_score": round(experience_score, 1),
        "format_score": round(format_score, 1),
        "ats_score": round(ats_score, 1),
    }


def generate_suggestions(parsed_data: Dict, scores: Dict, missing_skills: List[str]) -> List[Dict]:
    suggestions = []
    skills = parsed_data.get("skills", [])
    if scores["skills_score"] < 60:
        suggestions.append({"category": "skills", "severity": "critical",
            "message": f"Only {len(skills)} skills detected. Aim for 10+.",
            "action": f"Add: {', '.join(missing_skills[:5])}"})
    if scores["ats_score"] < 50:
        suggestions.append({"category": "keywords", "severity": "important",
            "message": "Low ATS compatibility. May be filtered out by automated systems.",
            "action": "Add keywords: REST API, microservices, CI/CD, agile, system design"})
    if not parsed_data.get("summary"):
        suggestions.append({"category": "content", "severity": "important",
            "message": "No professional summary found.",
            "action": "Add a 2-3 sentence summary highlighting expertise and goals."})
    if not parsed_data.get("github"):
        suggestions.append({"category": "content", "severity": "minor",
            "message": "No GitHub profile linked.",
            "action": "Add your GitHub URL to showcase projects."})
    if len(parsed_data.get("projects", [])) < 2:
        suggestions.append({"category": "content", "severity": "important",
            "message": "Fewer than 2 projects listed.",
            "action": "Add 2-4 projects with tech stack and impact metrics."})
    return suggestions