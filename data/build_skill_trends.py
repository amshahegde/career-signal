"""
Build a monthly skill-frequency table from the raw gsearch_jobs CSVs.
Run once to produce data/skill_monthly_counts.csv, which the
skill_decay module reads at runtime (keeps the app fast — no need to
re-parse 28k rows of raw postings on every request).
"""

import ast
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent
SOURCE_FILES = [
    "gsearch_jobs_2022.csv",
    "gsearch_jobs_2023_q1.csv",
    "gsearch_jobs_2023_q2.csv",
    "gsearch_jobs_2023_q3.csv",
]


def load_raw() -> pd.DataFrame:
    frames = []
    for fname in SOURCE_FILES:
        path = DATA_DIR / fname
        d = pd.read_csv(path, usecols=["date_time", "description_tokens"])
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["date_time"] = pd.to_datetime(df["date_time"], errors="coerce")
    df = df.dropna(subset=["date_time"])
    return df


def parse_tokens(raw: str) -> list[str]:
    try:
        val = ast.literal_eval(raw)
        if isinstance(val, list):
            return [str(x).strip().lower() for x in val if str(x).strip()]
    except (ValueError, SyntaxError):
        pass
    return []


def build_monthly_counts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["date_time"].dt.to_period("M").astype(str)
    df["skills"] = df["description_tokens"].apply(parse_tokens)

    # total postings per month (denominator for share-of-postings %)
    postings_per_month = df.groupby("month").size().rename("total_postings")

    exploded = df.explode("skills").dropna(subset=["skills"])
    exploded = exploded[exploded["skills"] != ""]

    skill_month_counts = (
        exploded.groupby(["month", "skills"]).size().rename("mentions").reset_index()
    )
    skill_month_counts = skill_month_counts.merge(
        postings_per_month, on="month", how="left"
    )
    skill_month_counts["share_pct"] = (
        skill_month_counts["mentions"] / skill_month_counts["total_postings"] * 100
    ).round(3)

    return skill_month_counts.sort_values(["skills", "month"])


if __name__ == "__main__":
    print("Loading raw postings...")
    raw = load_raw()
    print(f"Loaded {len(raw)} postings from {raw['date_time'].min()} to {raw['date_time'].max()}")

    print("Building monthly skill-frequency table...")
    monthly = build_monthly_counts(raw)

    out_path = DATA_DIR / "skill_monthly_counts.csv"
    monthly.to_csv(out_path, index=False)
    print(f"Saved {len(monthly)} rows to {out_path}")
    print(f"Unique skills tracked: {monthly['skills'].nunique()}")
    print(f"Months covered: {sorted(monthly['month'].unique())}")
