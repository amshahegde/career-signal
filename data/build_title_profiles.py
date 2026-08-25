"""
Build per-job-title skill profiles from the raw gsearch_jobs CSVs.
Titles are lightly normalized (lowercased, common suffixes like 'II'/'Sr.'
stripped) and filtered to those with enough postings for a reliable
skill profile. Output feeds the Career Pivot Finder module.
"""

import ast
import re
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent
SOURCE_FILES = [
    "gsearch_jobs_2022.csv",
    "gsearch_jobs_2023_q1.csv",
    "gsearch_jobs_2023_q2.csv",
    "gsearch_jobs_2023_q3.csv",
]

MIN_POSTINGS_PER_TITLE = 15
MAX_TITLE_WORDS = 5  # legitimate titles are short; longer strings are posting-boilerplate noise

SUFFIX_PATTERN = re.compile(
    r"\b(i{1,3}|iv|senior|sr\.?|junior|jr\.?|lead|principal|staff|"
    r"remote|hybrid|onsite|on site|on-site|contract|contract to hire|"
    r"to hire|c2h|now hiring|hiring now|available|urgent|immediate|"
    r"immediately|full time|part time|temp|temporary|w2|1099|new|"
    r"entry level|work from home|wfh)\b",
    re.IGNORECASE,
)
PAREN_PATTERN = re.compile(r"\(.*?\)")


def normalize_title(raw: str) -> str:
    t = str(raw).strip().lower()
    t = PAREN_PATTERN.sub("", t)
    t = SUFFIX_PATTERN.sub("", t)
    t = re.sub(r"[^a-z&\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_tokens(raw: str) -> list[str]:
    try:
        val = ast.literal_eval(raw)
        if isinstance(val, list):
            return [str(x).strip().lower() for x in val if str(x).strip()]
    except (ValueError, SyntaxError):
        pass
    return []


def load_raw() -> pd.DataFrame:
    frames = []
    for fname in SOURCE_FILES:
        d = pd.read_csv(DATA_DIR / fname, usecols=["title", "description_tokens"])
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def build_profiles(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["norm_title"] = df["title"].apply(normalize_title)
    df["skills"] = df["description_tokens"].apply(parse_tokens)

    posting_counts = df.groupby("norm_title").size().rename("posting_count")
    valid_titles = posting_counts[posting_counts >= MIN_POSTINGS_PER_TITLE].index
    valid_titles = [t for t in valid_titles if 0 < len(t.split()) <= MAX_TITLE_WORDS]

    df = df[df["norm_title"].isin(valid_titles)]
    exploded = df.explode("skills").dropna(subset=["skills"])
    exploded = exploded[exploded["skills"] != ""]

    profile = (
        exploded.groupby(["norm_title", "skills"]).size().rename("count").reset_index()
    )
    profile = profile.merge(posting_counts, on="norm_title", how="left")
    return profile.sort_values(["norm_title", "count"], ascending=[True, False])


if __name__ == "__main__":
    print("Loading raw postings...")
    raw = load_raw()
    print(f"Loaded {len(raw)} postings")

    print("Building normalized title-skill profiles...")
    profiles = build_profiles(raw)

    out_path = DATA_DIR / "title_skill_profiles.csv"
    profiles.to_csv(out_path, index=False)

    n_titles = profiles["norm_title"].nunique()
    print(f"Saved {len(profiles)} rows covering {n_titles} normalized titles "
          f"(min {MIN_POSTINGS_PER_TITLE} postings each) to {out_path}")
    print("\nTop titles by posting count:")
    print(
        profiles.drop_duplicates("norm_title")
        .sort_values("posting_count", ascending=False)
        .head(15)[["norm_title", "posting_count"]]
        .to_string(index=False)
    )
