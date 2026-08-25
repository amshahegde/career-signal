#!/usr/bin/env bash
# Downloads the raw source job-posting CSVs used to build data/skill_monthly_counts.csv
# and data/title_skill_profiles.csv. Not committed to git (too large) — run this once,
# then `python data/build_skill_trends.py` and `python data/build_title_profiles.py`
# to regenerate the derived datasets from scratch.
set -e
cd "$(dirname "$0")"

FILES=(
  "gsearch_jobs_2022.csv"
  "gsearch_jobs_2023_q1.csv"
  "gsearch_jobs_2023_q2.csv"
  "gsearch_jobs_2023_q3.csv"
)

for f in "${FILES[@]}"; do
  echo "Downloading $f..."
  curl -sL -o "$f" "https://raw.githubusercontent.com/iweld/data-analyst-job-postings/main/source_data/csv/$f"
done

echo "Done. Run: python build_skill_trends.py && python build_title_profiles.py"
