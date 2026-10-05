"""Question Intelligence v1 for Reads Football.

Pure, deterministic quality analysis layered above certified generators.
It never changes a certified correct answer. It scores wording/depth,
fingerprints repeats, estimates player-facing difficulty, and ranks
candidate distractors when Reads itself owns the distractor pool.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable

_GENERIC_PATTERNS = (
    "what was the record",
    "what was their record",
    "this event was classified as",
    "event was classified as",
    "event type",
    "taxonomy",
    "which team had this record",
)
_CONTEXT_WORDS = {
    "draft", "season", "playoff", "super bowl", "championship", "heisman",
    "touchdown", "yards", "ranking", "ranked", "coach", "coached", "rivalry",
    "interception", "sack", "fumble", "drive", "quarter", "conference",
    "college", "roster", "starter", "award", "bowl",
}
_REASONING_WORDS = {
    "before", "after", "later", "earlier", "while", "despite", "between",
    "following", "only", "first", "last", "also", "then",
}


def _norm(value: Any) -> str:
    s = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _tokens(value: Any) -> list[str]:
    return [t for t in _norm(value).split() if len(t) > 1]


def question_fingerprint(question: dict) -> str:
    """Exact-content fingerprint, stable across option order."""
    prompt = _norm(question.get("question") or question.get("prompt"))
    answer = _norm(
        question.get("answer")
        or question.get("correct_label")
        or ((question.get("answer") or {}).get("label") if isinstance(question.get("answer"), dict) else "")
    )
    if isinstance(question.get("answer"), dict):
        answer = _norm(question["answer"].get("label"))
    payload = prompt + "|" + answer
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def semantic_fingerprint(question: dict) -> str:
    """Near-repeat family fingerprint.

    Years/numbers and common glue words are removed so the same fact template
    asked with a nearby season/player is detectable without pretending to be
    full semantic embedding.
    """
    prompt = _norm(question.get("question") or question.get("prompt"))
    prompt = re.sub(r"\b(?:19|20)\d{2}\b", "YEAR", prompt)
    prompt = re.sub(r"\b\d+\b", "NUM", prompt)
    stop = {"the","a","an","did","does","do","was","were","is","are","which","what","who","in","of","for","to"}
    toks = [t for t in prompt.split() if t not in stop]
    return hashlib.sha256(" ".join(toks).encode("utf-8")).hexdigest()[:20]


def _option_labels(question: dict) -> list[str]:
    opts = question.get("options") or question.get("decoy_labels") or []
    if question.get("decoy_labels") is not None and question.get("correct_label") is not None:
        opts = [question.get("correct_label")] + list(question.get("decoy_labels") or [])
    out = []
    for x in opts:
        if isinstance(x, dict):
            x = x.get("label")
        if x is not None:
            out.append(str(x))
    return out


def score_question(question: dict, *, source: str | None = None) -> dict:
    prompt = str(question.get("question") or question.get("prompt") or "").strip()
    low = _norm(prompt)
    labels = _option_labels(question)
    score = 42
    reasons: list[str] = []

    if len(prompt) >= 45:
        score += 8; reasons.append("specific wording")
    if len(prompt) >= 80:
        score += 5; reasons.append("rich context")
    if re.search(r"\b(?:19|20)\d{2}\b", prompt):
        score += 6; reasons.append("season/year context")
    context_hits = sum(1 for w in _CONTEXT_WORDS if w in low)
    score += min(12, context_hits * 3)
    if context_hits >= 2:
        reasons.append("multi-context football fact")
    reasoning_hits = sum(1 for w in _REASONING_WORDS if re.search(r"\b"+re.escape(w)+r"\b", low))
    score += min(12, reasoning_hits * 4)
    if reasoning_hits:
        reasons.append("reasoning/relationship wording")
    properish = len(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", prompt))
    score += min(8, properish * 4)
    if properish:
        reasons.append("named-entity context")

    if any(p in low for p in _GENERIC_PATTERNS):
        score -= 28; reasons.append("generic/metadata wording")
    if low.startswith("this event") or low.startswith("this player") or low.startswith("this team"):
        score -= 8; reasons.append("vague subject")
    if len(prompt) < 28:
        score -= 10; reasons.append("too little context")

    if labels:
        normalized = [_norm(x) for x in labels]
        if len(set(normalized)) != len(normalized):
            score -= 25; reasons.append("duplicate options")
        else:
            score += 4
        if len(labels) >= 4:
            score += 3
        lens = [max(1, len(_tokens(x))) for x in labels]
        if max(lens) - min(lens) <= 2:
            score += 5; reasons.append("plausible option shape")
        elif max(lens) >= min(lens) * 4:
            score -= 6; reasons.append("giveaway option shape")

    src = str(source or question.get("depth_source") or question.get("source") or "")
    if src and src.upper() not in {"", "UNKNOWN"}:
        score += 5; reasons.append("source-backed")

    score = max(0, min(100, score))
    if score >= 82:
        tier = "impossible"
    elif score >= 68:
        tier = "sicko"
    elif score >= 54:
        tier = "competitive"
    else:
        tier = "casual"
    return {
        "score": score,
        "tier": tier,
        "fingerprint": question_fingerprint(question),
        "semantic_fingerprint": semantic_fingerprint(question),
        "reasons": reasons,
    }


def quality_gate(question: dict, *, min_score: int = 50, source: str | None = None) -> tuple[bool, dict]:
    meta = score_question(question, source=source)
    return meta["score"] >= int(min_score), meta


def _candidate_label(candidate: Any) -> str:
    return str(candidate.get("label") if isinstance(candidate, dict) else candidate)


def _candidate_tags(candidate: Any) -> set[str]:
    if not isinstance(candidate, dict):
        return set()
    tags = candidate.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return {_norm(x) for x in tags if _norm(x)}


def select_smart_distractors(correct: Any, candidates: Iterable[Any], *, count: int = 3, seed: str = "") -> list[str]:
    """Pick plausible, deterministic distractors from a caller-owned pool."""
    correct_label = _candidate_label(correct)
    correct_norm = _norm(correct_label)
    correct_tokens = set(_tokens(correct_label))
    correct_tags = _candidate_tags(correct)
    correct_numeric = bool(re.fullmatch(r"[\d .%+-]+", correct_label.strip()))
    ranked = []
    seen = {correct_norm}
    for cand in candidates:
        label = _candidate_label(cand)
        norm = _norm(label)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        toks = set(_tokens(label))
        tags = _candidate_tags(cand)
        numeric = bool(re.fullmatch(r"[\d .%+-]+", label.strip()))
        lexical = len(correct_tokens & toks) / max(1, len(correct_tokens | toks))
        length_similarity = 1.0 - min(1.0, abs(len(label)-len(correct_label)) / max(1, len(correct_label)))
        word_similarity = 1.0 - min(1.0, abs(len(toks)-len(correct_tokens)) / max(1, len(correct_tokens)))
        tag_overlap = len(correct_tags & tags) / max(1, len(correct_tags | tags)) if (correct_tags or tags) else 0.0
        type_match = 1.0 if numeric == correct_numeric else 0.0
        tie = int(hashlib.sha256((seed+"|"+norm).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        score = 4*tag_overlap + 2*type_match + 1.5*word_similarity + length_similarity + lexical + 0.01*tie
        ranked.append((score, label))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return [label for _, label in ranked[:max(0, int(count))]]


def annotate_package(package: dict) -> dict:
    """Attach intelligence metadata without altering certified truth."""
    questions = package.get("questions")
    if not isinstance(questions, list):
        return package
    scores = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        meta = score_question(q)
        q["question_intelligence"] = meta
        scores.append(meta["score"])
    package["question_intelligence"] = {
        "version": 1,
        "question_count": len(scores),
        "average_score": round(sum(scores)/len(scores), 1) if scores else None,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
    }
    return package
