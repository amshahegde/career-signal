"""
Daily Skill Snapshot Collector (RemoteOK)
-------------------------------------------
Pulls the free public RemoteOK job feed and records skill-tag frequency
for today's date. Intended to run once per day via a GitHub Actions cron
job (see .github/workflows/collect_skill_data.yml), accumulating real
history over time so skill_decay.py has genuinely current data to trend on.

Attribution note (per RemoteOK API Terms of Service): this script only
extracts aggregate tag-frequency statistics for internal trend analysis
and does not republish job descriptions. If displaying individual job
listings anywhere in the app, link back to the original RemoteOK URL.
Source: https://remoteok.com/api
"""

import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

API_URL = "https://remoteok.com/api"
OUT_PATH = Path(__file__).parent.parent.parent / "data" / "live_skill_snapshots.csv"
FIELDNAMES = ["snapshot_date", "skill", "mentions", "total_postings", "share_pct"]


def fetch_postings() -> list[dict]:
    resp = requests.get(API_URL, headers={"User-Agent": "career-intelligence-toolkit/1.0"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # First element is a metadata/legal notice, not a job posting — skip it.
    return [item for item in data if "tags" in item and "position" in item]


def build_snapshot(postings: list[dict], snapshot_date: str) -> list[dict]:
    total = len(postings)
    if total == 0:
        return []

    tag_counts: dict[str, int] = {}
    for posting in postings:
        for tag in posting.get("tags", []):
            tag = tag.strip().lower()
            if not tag:
                continue
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    rows = []
    for tag, count in sorted(tag_counts.items()):
        rows.append({
            "snapshot_date": snapshot_date,
            "skill": tag,
            "mentions": count,
            "total_postings": total,
            "share_pct": round(count / total * 100, 3),
        })
    return rows


def append_snapshot(rows: list[dict]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = OUT_PATH.exists()
    with open(OUT_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main():
    snapshot_date = date.today().isoformat()
    print(f"Fetching RemoteOK postings for snapshot date {snapshot_date}...")
    postings = fetch_postings()
    print(f"Fetched {len(postings)} postings.")

    rows = build_snapshot(postings, snapshot_date)
    if not rows:
        print("No postings/tags found — skipping write.")
        sys.exit(1)

    append_snapshot(rows)
    print(f"Appended {len(rows)} skill rows for {snapshot_date} to {OUT_PATH}")


if __name__ == "__main__":
    main()
