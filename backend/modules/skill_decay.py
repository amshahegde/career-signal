"""
Skill Decay Predictor
----------------------
Measures skill "momentum" using a trend-slope approach: fit a linear
regression of a skill's monthly share-of-postings (%) over time, and use
the slope as the momentum signal.

- Positive slope, statistically meaningful  -> RISING
- Negative slope, statistically meaningful   -> DECLINING
- Near-zero slope / too little data          -> STABLE / INSUFFICIENT_DATA

This is deliberately a *relative* signal (share of postings, not raw
mention count), so it isn't confounded by the total number of postings
scraped changing month to month.
"""

from pathlib import Path
import pandas as pd
import numpy as np

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "skill_monthly_counts.csv"

MIN_MONTHS_FOR_TREND = 4          # need at least this many months of data
SLOPE_STABLE_THRESHOLD = 0.03     # pct-point/month change below this = "stable"


def _load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    return df


_DATA_CACHE: pd.DataFrame | None = None


def _get_data() -> pd.DataFrame:
    global _DATA_CACHE
    if _DATA_CACHE is None:
        _DATA_CACHE = _load_data()
    return _DATA_CACHE


def _fit_trend_slope(months: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    """Fit a simple linear regression (month index -> share_pct).
    Returns (slope, r_squared)."""
    if len(months) < 2:
        return 0.0, 0.0
    x = months.astype(float)
    x = x - x.min()  # normalize to start at 0
    y = values.astype(float)
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return round(float(slope), 5), round(float(r_squared), 3)


def analyze_skill(skill: str) -> dict:
    df = _get_data()
    skill = skill.strip().lower()
    subset = df[df["skills"] == skill].sort_values("month")

    if len(subset) < MIN_MONTHS_FOR_TREND:
        return {
            "skill": skill,
            "status": "INSUFFICIENT_DATA",
            "months_tracked": len(subset),
            "message": f"Only {len(subset)} month(s) of data — need at least "
                       f"{MIN_MONTHS_FOR_TREND} to compute a reliable trend.",
        }

    month_idx = subset["month"].apply(lambda p: p.ordinal).to_numpy()
    shares = subset["share_pct"].to_numpy()

    slope, r_squared = _fit_trend_slope(month_idx, shares)

    if abs(slope) < SLOPE_STABLE_THRESHOLD:
        status = "STABLE"
    elif slope > 0:
        status = "RISING"
    else:
        status = "DECLINING"

    return {
        "skill": skill,
        "status": status,
        "months_tracked": len(subset),
        "slope_pct_per_month": slope,
        "trend_fit_r2": r_squared,
        "current_share_pct": round(float(shares[-1]), 3),
        "history": [
            {"month": str(m), "share_pct": round(float(s), 3)}
            for m, s in zip(subset["month"], shares)
        ],
    }


def analyze_skills(skills: list[str]) -> dict:
    """Analyze a list of skills (e.g. extracted from a resume) and return
    momentum status for each, sorted by most concerning (declining) first."""
    results = [analyze_skill(s) for s in skills]

    status_order = {"DECLINING": 0, "STABLE": 1, "INSUFFICIENT_DATA": 2, "RISING": 3}
    results.sort(key=lambda r: (status_order.get(r["status"], 4), r.get("slope_pct_per_month", 0)))

    declining = [r["skill"] for r in results if r["status"] == "DECLINING"]
    rising = [r["skill"] for r in results if r["status"] == "RISING"]

    return {
        "skills_analyzed": len(results),
        "declining_skills": declining,
        "rising_skills": rising,
        "details": results,
    }


def top_rising_and_declining(n: int = 10) -> dict:
    """Utility for exploring the dataset: what's rising/declining overall,
    independent of any specific resume."""
    df = _get_data()
    all_skills = df["skills"].unique().tolist()
    analyzed = [analyze_skill(s) for s in all_skills]
    valid = [a for a in analyzed if a["status"] in ("RISING", "DECLINING", "STABLE")]

    rising = sorted(
        [a for a in valid if a["status"] == "RISING"],
        key=lambda a: -a["slope_pct_per_month"],
    )[:n]
    declining = sorted(
        [a for a in valid if a["status"] == "DECLINING"],
        key=lambda a: a["slope_pct_per_month"],
    )[:n]
    return {"top_rising": rising, "top_declining": declining}


if __name__ == "__main__":
    import json

    print("=== Top rising & declining skills in the dataset ===")
    print(json.dumps(top_rising_and_declining(5), indent=2))

    print("\n=== Example: analyzing a resume's skill list ===")
    resume_skills = ["python", "excel", "power_bi", "sql", "spss", "tableau"]
    print(json.dumps(analyze_skills(resume_skills), indent=2))
