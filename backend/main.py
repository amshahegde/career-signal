"""
Career Intelligence Toolkit — FastAPI backend
------------------------------------------------
Single entry point tying together:
  1. weak_language   — resume phrasing analysis
  2. skill_decay      — skill market-momentum analysis
  3. career_pivot     — adjacent job title discovery

Run with: uvicorn main:app --reload
"""

import tempfile
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules import weak_language, skill_decay, career_pivot, resume_parser

app = FastAPI(title="Career Intelligence Toolkit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_skill_vocabulary() -> set[str]:
    decay_vocab = set(pd.read_csv(DATA_DIR / "skill_monthly_counts.csv")["skills"].unique())
    pivot_vocab = set(pd.read_csv(DATA_DIR / "title_skill_profiles.csv")["skills"].unique())
    return decay_vocab | pivot_vocab


SKILL_VOCAB = _load_skill_vocabulary()


class BulletsRequest(BaseModel):
    bullets: list[str]


class SkillsRequest(BaseModel):
    skills: list[str]


class TitleRequest(BaseModel):
    title: str


@app.get("/health")
def health():
    return {"status": "ok", "skill_vocabulary_size": len(SKILL_VOCAB)}


@app.post("/analyze/weak-language")
def analyze_weak_language(req: BulletsRequest):
    return weak_language.analyze_resume(req.bullets)


@app.post("/analyze/skill-decay")
def analyze_skill_decay(req: SkillsRequest):
    return skill_decay.analyze_skills(req.skills)


@app.post("/analyze/career-pivot")
def analyze_career_pivot(req: SkillsRequest):
    return {"matched_titles": career_pivot.find_titles_for_skills(req.skills)}


@app.post("/analyze/career-pivot/from-title")
def analyze_career_pivot_from_title(req: TitleRequest):
    return career_pivot.find_adjacent_titles(req.title)


@app.post("/analyze/resume")
async def analyze_full_resume(file: UploadFile = File(...)):
    """One-shot endpoint: upload a resume PDF, get all three analyses back."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF resumes are supported right now.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        parsed = resume_parser.parse_resume(tmp_path, SKILL_VOCAB)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not parsed["bullets"]:
        raise HTTPException(422, "Couldn't extract bullet points from this resume.")

    weak_language_report = weak_language.analyze_resume(parsed["bullets"])
    skill_decay_report = skill_decay.analyze_skills(parsed["skills"]) if parsed["skills"] else None
    pivot_report = career_pivot.find_titles_for_skills(parsed["skills"]) if parsed["skills"] else []

    return {
        "extracted_bullets_count": len(parsed["bullets"]),
        "extracted_skills": parsed["skills"],
        "weak_language": weak_language_report,
        "skill_decay": skill_decay_report,
        "career_pivot": {"matched_titles": pivot_report},
    }
