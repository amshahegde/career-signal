"""
Resume Parser
--------------
Extracts (1) bullet points and (2) mentioned skills from raw resume text,
so a single resume upload can feed all three analysis modules:
  - bullets  -> weak_language.analyze_resume()
  - skills   -> skill_decay.analyze_skills() and career_pivot.find_titles_for_skills()
"""

import re
from pathlib import Path

from pypdf import PdfReader

BULLET_MARKERS = ("•", "-", "*", "◦", "‣", "·")


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_bullets(text: str) -> list[str]:
    """Pull out lines that look like resume bullet points. Falls back to
    treating reasonably long lines as bullets if no explicit markers are
    found (some PDF extractors strip bullet glyphs)."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    explicit = [
        l.lstrip("".join(BULLET_MARKERS)).strip()
        for l in lines
        if l.startswith(BULLET_MARKERS)
    ]
    if explicit:
        return explicit

    # Fallback: lines starting with a capitalized past-tense-looking verb
    # and of reasonable bullet length.
    candidates = [
        l for l in lines
        if 40 <= len(l) <= 300 and re.match(r"^[A-Z][a-z]+ed\b", l)
    ]
    return candidates


def extract_skills(text: str, vocabulary: set[str]) -> list[str]:
    """Scan text for mentions of known skills, matching case-insensitively
    with boundary checks that work for skill names containing special
    characters (e.g. 'c++', 'asp.net') where standard \\b regex boundaries
    behave oddly."""
    lowered = text.lower()
    found = []
    for skill in vocabulary:
        skill_l = skill.lower()
        start = 0
        while True:
            idx = lowered.find(skill_l, start)
            if idx == -1:
                break
            before = lowered[idx - 1] if idx > 0 else " "
            after_idx = idx + len(skill_l)
            after = lowered[after_idx] if after_idx < len(lowered) else " "
            if not before.isalnum() and not after.isalnum():
                found.append(skill)
                break
            start = idx + 1
    return sorted(set(found))


def parse_resume(pdf_path: str, skill_vocabulary: set[str]) -> dict:
    text = extract_text_from_pdf(pdf_path)
    bullets = extract_bullets(text)
    skills = extract_skills(text, skill_vocabulary)
    return {
        "raw_text": text,
        "bullets": bullets,
        "skills": skills,
    }
