"""
Career Pivot Finder
---------------------
Finds job titles that share significant skill overlap with either:
  (a) a given list of skills (e.g. extracted from a resume), or
  (b) a given current job title

Approach: build a title x skill matrix from real posting data, TF-IDF
weight it (so common skills like "excel" don't dominate every match),
and use cosine similarity to rank the closest titles. This is skill-DNA
matching, not black-box semantic embeddings — deliberately explainable:
every match can point to the exact overlapping skills that drove it.
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "title_skill_profiles.csv"

_CACHE = {}


def _load():
    if "profiles" in _CACHE:
        return _CACHE["profiles"], _CACHE["matrix"], _CACHE["vectorizer"], _CACHE["titles"]

    df = pd.read_csv(DATA_PATH)

    # Build a "document" per title: skill repeated `count` times so TF-IDF
    # naturally weights by how central that skill is to the title.
    docs = []
    titles = []
    for title, group in df.groupby("norm_title"):
        tokens = []
        for _, row in group.iterrows():
            tokens.extend([row["skills"]] * int(row["count"]))
        docs.append(" ".join(tokens))
        titles.append(title)

    vectorizer = TfidfVectorizer(token_pattern=r"[^\s]+")
    matrix = vectorizer.fit_transform(docs)

    _CACHE.update({"profiles": df, "matrix": matrix, "vectorizer": vectorizer, "titles": titles})
    return df, matrix, vectorizer, titles


def find_titles_for_skills(skills: list[str], top_n: int = 8) -> list[dict]:
    """Given a list of skills (e.g. from a resume), rank the job titles
    with the most similar skill profile."""
    df, matrix, vectorizer, titles = _load()

    query = " ".join(s.strip().lower() for s in skills)
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, matrix)[0]

    ranked_idx = np.argsort(-sims)[:top_n]
    results = []
    for idx in ranked_idx:
        title = titles[idx]
        title_skills = set(df[df["norm_title"] == title]["skills"])
        overlap = sorted(set(s.lower() for s in skills) & title_skills)
        results.append({
            "title": title,
            "similarity": round(float(sims[idx]), 4),
            "overlapping_skills": overlap,
            "posting_count": int(df[df["norm_title"] == title]["posting_count"].iloc[0]),
        })
    return results


def find_adjacent_titles(current_title: str, top_n: int = 5) -> dict:
    """Given a current job title (normalized or free text), find the
    most skill-similar OTHER titles — i.e. plausible pivot targets."""
    df, matrix, vectorizer, titles = _load()

    current_title_norm = current_title.strip().lower()
    if current_title_norm not in titles:
        # fall back to matching on the title's own skill set via substring
        matches = [t for t in titles if current_title_norm in t or t in current_title_norm]
        if not matches:
            return {
                "current_title": current_title,
                "status": "TITLE_NOT_FOUND",
                "message": f"'{current_title}' isn't in our tracked title set. "
                           f"Try find_titles_for_skills() with your skill list instead.",
            }
        current_title_norm = matches[0]

    idx = titles.index(current_title_norm)
    sims = cosine_similarity(matrix[idx], matrix)[0]
    sims[idx] = -1  # exclude self

    ranked_idx = np.argsort(-sims)[:top_n]
    pivots = []
    current_skills = set(df[df["norm_title"] == current_title_norm]["skills"])
    for i in ranked_idx:
        target_title = titles[i]
        target_skills = set(df[df["norm_title"] == target_title]["skills"])
        overlap = sorted(current_skills & target_skills)
        gap = sorted(target_skills - current_skills)[:5]  # top skills to learn
        pivots.append({
            "title": target_title,
            "similarity": round(float(sims[i]), 4),
            "shared_skills": overlap,
            "skills_to_learn": gap,
        })

    return {
        "current_title": current_title_norm,
        "status": "OK",
        "pivot_options": pivots,
    }


if __name__ == "__main__":
    import json

    print("=== Example: titles matching a resume's skill list ===")
    resume_skills = ["python", "sql", "tableau", "excel", "power_bi", "statistics"]
    print(json.dumps(find_titles_for_skills(resume_skills, top_n=5), indent=2))

    print("\n=== Example: pivot options from 'data analyst' ===")
    print(json.dumps(find_adjacent_titles("data analyst", top_n=5), indent=2))
