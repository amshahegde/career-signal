"""One-off seed script: builds today's snapshot from the RemoteOK postings
already retrieved in this session (since this sandbox can't reach
remoteok.com directly). Going forward, the GitHub Actions workflow will
fetch live directly — this just seeds real day-one data so the pipeline
isn't starting from nothing."""

import sys
sys.path.insert(0, "/home/claude/career-intelligence-toolkit/backend/collectors")
from remoteok_collector import build_snapshot, append_snapshot

# Tags extracted from the real RemoteOK API response fetched 2026-08-25
postings = [
    {"tags": ["design","education","technical","customer support","dev","exec","senior","ops","excel","engineer","digital nomad","marketing","virtual assistant","medical"]},
    {"tags": ["education","technical","exec","ops"]},
    {"tags": ["finance","medical","non tech"]},
    {"tags": ["education","non tech"]},
    {"tags": ["education","customer support","dev","exec","math","node","ops","sales","medical","digital nomad"]},
    {"tags": ["hr","sys admin","customer support","marketing","education","exec","senior","medical","engineer","recruiter","full time"]},
    {"tags": ["education","non tech","design","marketing","digital nomad"]},
    {"tags": ["exec","customer support","dev","excel","engineer","full time","digital nomad"]},
    {"tags": ["education","medical","non tech"]},
    {"tags": ["education","non tech"]},
    {"tags": ["exec","customer support","testing","finance","sales","recruiter"]},
    {"tags": ["exec","customer support","dev","excel","engineer","full time","digital nomad","design","content writing","education"]},
    {"tags": []},
    {"tags": ["full stack","front end","python","dev","testing","web dev","quality assurance","devops","c","cloud","nosql","git","flutter","angular","mobile","golang","backend","digital nomad"]},
    {"tags": ["analyst","design","saas","infosec","education","technical","dev","cloud","exec","senior","ops","marketing","engineer","digital nomad"]},
    {"tags": ["education","non tech","design","marketing","digital nomad"]},
    {"tags": ["exec","customer support","dev","excel","engineer","full time","digital nomad"]},
    {"tags": ["education","medical","non tech"]},
    {"tags": ["exec","customer support","dev","medical","digital nomad"]},
    {"tags": ["design","dev","travel","finance","scheme","microsoft","exec","excel","full time","digital nomad"]},
    {"tags": ["design","sys admin","education","customer support","testing","travel","node","microsoft","exec","ops","medical","engineer","digital nomad","c sharp","technical","marketing","quality assurance","javascript","c","css","html"]},
    {"tags": ["marketing","non tech"]},
    {"tags": ["education","customer support","dev","marketing","exec","medical","recruiter","digital nomad"]},
    {"tags": ["customer support","non tech","education","golang","medical","full time"]},
    {"tags": ["virtual assistant","customer support","marketing","travel","speech","finance","medical","recruiter","non tech","exec","infosec","education","ops","sales","golang"]},
    {"tags": ["customer support","non tech"]},
    {"tags": ["virtual assistant","customer support","marketing","travel","speech","finance","medical","recruiter","non tech"]},
    {"tags": ["virtual assistant","customer support","marketing","travel","speech","finance","medical","recruiter","non tech","exec","infosec","education","ops","sales","golang"]},
    {"tags": ["design","sys admin","education","customer support","testing","travel","node","microsoft","exec","ops","medical","engineer","digital nomad"]},
    {"tags": ["sales","non tech","customer support","microsoft","ops","excel","recruiter","full time","dev","exec","medical","digital nomad"]},
    {"tags": ["exec","medical"]},
    {"tags": ["accounting","infosec"]},
    {"tags": ["design","customer support","marketing","exec","virtual assistant","sales","medical","full time","digital nomad"]},
    {"tags": ["customer support","medical","non tech"]},
]

rows = build_snapshot(postings, "2026-08-25")
append_snapshot(rows)
print(f"Seeded {len(rows)} skill rows for 2026-08-25")

# quick sanity check
import csv
with open("/home/claude/career-intelligence-toolkit/data/live_skill_snapshots.csv") as f:
    reader = list(csv.DictReader(f))
    print(f"Total rows in file: {len(reader)}")
    top5 = sorted(reader, key=lambda r: -float(r["share_pct"]))[:5]
    for r in top5:
        print(r)
