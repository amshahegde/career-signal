# Career Signal — Career Intelligence Toolkit

A web app that reads the job market on your resume: it flags phrasing that
undersells you, tracks which of your skills are gaining or losing ground,
and finds job titles you're already largely qualified for — all from real
job-posting data.

**Live demo:** _add your deployed URL here_
**Screenshot:** _add a screenshot here_

## What it does

| Module | What it answers | How |
|---|---|---|
| **Weak-Language Detector** | "Is my resume phrasing undermining my achievements?" | NLP scan (spaCy) for passive voice, hedging language, weak verbs, and missing quantification, per bullet, with concrete rewrite suggestions |
| **Skill Decay Predictor** | "Which of my skills are fading vs. rising in the job market?" | Trend-slope regression on real monthly skill-mention frequency from ~28k job postings |
| **Career Pivot Finder** | "What job title am I already qualified for that I haven't considered?" | TF-IDF + cosine similarity over skill profiles built from real postings, per job title |

## Architecture

```
career-intelligence-toolkit/
├── backend/               FastAPI app
│   ├── main.py             API endpoints tying the 3 modules together
│   ├── modules/
│   │   ├── weak_language.py
│   │   ├── skill_decay.py
│   │   ├── career_pivot.py
│   │   └── resume_parser.py   PDF → bullets + recognized skills
│   └── collectors/
│       └── remoteok_collector.py  daily live-data collector (see below)
├── frontend/               Static site (nginx-served), calls the API directly
├── data/                   Preprocessed datasets (see Data Sources)
├── .github/workflows/      Daily data-collection automation
└── docker-compose.yml      Runs backend + frontend together
```

## Running it

```bash
docker compose up --build
```

Then open **http://localhost** — the frontend calls the backend automatically
(nginx proxies `/analyze/*` and `/health` to the backend container).

To run the backend alone for development:

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```

## Data sources & honest limitations

This project is built on **real data, not synthetic placeholders** — but
it's important to be upfront about scope:

- **Skill Decay & Career Pivot** are trained on [~28k Data Analyst job
  postings scraped Nov 2022–Sep 2023](https://github.com/iweld/data-analyst-job-postings).
  This means: (a) trend/pivot results are most reliable for
  data-analyst-adjacent skills and titles, and thinner for other domains
  (e.g. specialized ML/CV tooling), and (b) the trend data has a fixed
  historical vintage — it is **not live** by default.
- **Weak-Language Detector** works on any resume text; it has no dataset
  dependency.
- A **daily live-data collector** (`backend/collectors/remoteok_collector.py`)
  pulls the free RemoteOK public API and appends a same-day skill-frequency
  snapshot to `data/live_skill_snapshots.csv`. A GitHub Actions workflow
  (`.github/workflows/collect_skill_data.yml`) runs this daily once the repo
  is pushed to GitHub, so the live dataset builds real history over time.
  **It needs a few months of daily runs before it's deep enough to compute
  a reliable trend** — this is intentional; the app reports
  `INSUFFICIENT_DATA` rather than fabricating a trend from too little data.
- Attribution: skill-trend data derived from RemoteOK's public API
  (https://remoteok.com/api) is aggregate/statistical only, per their API
  terms — no individual job listings are republished.

## Roadmap

- [ ] Swap in a domain-specific (ML/AI role) dataset once available, to
      widen Skill Decay / Career Pivot coverage beyond data-analyst roles
- [ ] Let the live collector accumulate enough history to become the
      primary trend source, phasing out the fixed 2022–2023 dataset
- [ ] Passive-voice and weak-verb rule expansion in the Weak-Language module
- [ ] Deploy live demo (Render/Railway/Fly.io)

## Tech stack

Python · FastAPI · spaCy · scikit-learn · pandas · nginx · Docker ·
GitHub Actions · vanilla JS/HTML/CSS frontend
