"""
Weak-Language Detector
-----------------------
Analyzes resume bullet points for phrasing that undersells achievements:
- Passive voice
- Hedging / weak qualifier words
- Weak verbs (vs. strong action verbs)
- Missing quantification (no numbers/metrics)

Returns a structured report per bullet with issues found and suggestions.
"""

import re
import spacy

nlp = spacy.load("en_core_web_sm")

HEDGE_WORDS = {
    "helped", "assisted", "involved in", "participated in", "responsible for",
    "worked on", "tried to", "attempted to", "somewhat", "various",
    "several", "some", "a few", "basically", "kind of", "sort of",
    "in charge of", "may have", "fairly", "quite", "just", "simply",
    "worked to", "a little", "supported the", "contributed to",
}

WEAK_VERBS = {
    "did", "made", "got", "worked", "handled", "used", "helped",
    "was involved", "participated", "assisted", "supported", "contributed",
}

STRONG_VERB_SUGGESTIONS = {
    "did": ["executed", "delivered", "drove"],
    "made": ["built", "engineered", "created", "produced"],
    "got": ["achieved", "secured", "attained"],
    "worked": ["led", "developed", "collaborated on", "executed"],
    "handled": ["managed", "owned", "directed"],
    "used": ["leveraged", "applied", "utilized"],
    "helped": ["drove", "enabled", "accelerated"],
    "supported": ["enabled", "sustained", "reinforced"],
    "contributed": ["delivered", "drove", "spearheaded"],
}

NUMBER_PATTERN = re.compile(r"\d+(\.\d+)?%?|\$\d+")


def _detect_passive_voice(doc) -> list[str]:
    """Detect passive voice constructions using dependency parse."""
    issues = []
    for token in doc:
        if token.dep_ == "nsubjpass":
            issues.append(
                f"Passive construction detected around '{token.head.text}' "
                f"— consider rewriting in active voice."
            )
    return issues


def _detect_hedging(text: str) -> list[str]:
    """Detect hedge words/phrases as standalone words, excluding cases where
    they're part of a hyphenated compound (e.g. 'assisted' inside
    'AI-assisted', which is a plain '\\b' word boundary and would still
    match since a hyphen counts as a boundary too)."""
    issues = []
    lowered = text.lower()
    for phrase in HEDGE_WORDS:
        pattern = r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])"
        if re.search(pattern, lowered):
            issues.append(f"Hedging/weak phrase found: '{phrase}'")
    return issues


def _detect_weak_verbs(doc) -> list[dict]:
    findings = []
    for token in doc:
        if token.pos_ == "VERB" and token.lemma_.lower() in WEAK_VERBS:
            suggestions = STRONG_VERB_SUGGESTIONS.get(token.lemma_.lower(), [])
            findings.append({
                "verb": token.text,
                "suggestions": suggestions,
            })
    return findings


def _detect_missing_quantification(text: str) -> bool:
    return NUMBER_PATTERN.search(text) is None


def _detect_weak_opener(doc) -> str | None:
    """Check whether the bullet opens with a strong action verb, per
    standard resume-writing guidance. Skips checks that would false-positive
    on legitimate non-verb openers (e.g. bullets starting with a proper noun
    or tool name, which we don't want to flag)."""
    if len(doc) == 0:
        return None
    first = doc[0]
    # skip check if first token is punctuation/whitespace artifact
    if first.is_punct or first.is_space:
        return None
    if first.pos_ == "VERB":
        return None
    if first.pos_ == "AUX":
        return "Bullet opens with an auxiliary verb (e.g. 'Was', 'Is') — start with a strong action verb instead."
    # Only flag other openers if they look like a generic/weak start
    # (avoids flagging bullets that legitimately open with a noun/tool name)
    if first.lemma_.lower() in {"responsible", "in", "helped", "assisted"}:
        return f"Bullet doesn't open with a strong action verb (starts with '{first.text}')."
    return None


def analyze_bullet(text: str) -> dict:
    """Run full analysis on a single resume bullet point."""
    doc = nlp(text)

    passive_issues = _detect_passive_voice(doc)
    hedge_issues = _detect_hedging(text)
    weak_verbs = _detect_weak_verbs(doc)
    missing_numbers = _detect_missing_quantification(text)
    weak_opener = _detect_weak_opener(doc)

    # simple scoring: start at 100, deduct per issue category
    score = 100
    if passive_issues:
        score -= 20
    if hedge_issues:
        score -= 15 * min(len(hedge_issues), 2)
    if weak_verbs:
        score -= 15
    if missing_numbers:
        score -= 20
    if weak_opener:
        score -= 15
    score = max(score, 0)

    suggestions = []
    if passive_issues:
        suggestions.append("Rewrite in active voice — start with a strong action verb.")
    if weak_verbs:
        verb_examples = ", ".join(
            f"'{w['verb']}' → {', '.join(w['suggestions'][:2])}" for w in weak_verbs
        )
        suggestions.append(f"Swap weak verbs for stronger ones: {verb_examples}")
    if hedge_issues:
        suggestions.append("Remove hedging language — state your contribution directly.")
    if missing_numbers:
        suggestions.append("Add a quantified result (%, $, time saved, team size, etc.)")
    if weak_opener:
        suggestions.append(weak_opener)

    return {
        "original": text,
        "score": score,
        "issues": {
            "passive_voice": passive_issues,
            "hedging": hedge_issues,
            "weak_verbs": weak_verbs,
            "missing_quantification": missing_numbers,
            "weak_opener": weak_opener,
        },
        "suggestions": suggestions,
    }


def analyze_resume(bullets: list[str]) -> dict:
    """Analyze a list of resume bullet points and return an aggregate report."""
    results = [analyze_bullet(b) for b in bullets if b.strip()]
    avg_score = round(sum(r["score"] for r in results) / len(results), 1) if results else 0
    return {
        "overall_score": avg_score,
        "bullets": results,
    }


if __name__ == "__main__":
    sample_bullets = [
        "Was responsible for helping the team with various tasks related to the project.",
        "Reduced deployment time by 40% by building a CI/CD pipeline with GitHub Actions.",
        "Helped organize some meetings and was involved in planning.",
    ]
    report = analyze_resume(sample_bullets)
    import json
    print(json.dumps(report, indent=2))
