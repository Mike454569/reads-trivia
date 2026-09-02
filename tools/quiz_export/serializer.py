"""Option finalization and deterministic JS serialization.

finalize_options() is the exact 4-line shuffle-and-index block that was
byte-identical across all three original scripts. It must be called at the
same point in an adapter's evaluate() sequence as the original script called
it (after the options-uniqueness check and the question-duplicate check,
per every original script) -- see the RNG-order-preservation note in
QUIZ_EXPORT_FRAMEWORK_REFACTOR_PLAN.md.

write_quiz_js() reproduces the exact header/body/footer shape used by all
three originals; only the header text and global name are domain-supplied.
"""
from __future__ import annotations

import json
from pathlib import Path

CONTRACT_KEY_ORDER = ("id", "category", "difficulty", "question", "options", "correctIndex", "notes")


def finalize_options(rng, correct_text: str, distractor_texts: list[str]):
    options = [correct_text] + list(distractor_texts)
    order = list(range(4))
    rng.shuffle(order)
    shuffled_options = [options[i] for i in order]
    correct_index = shuffled_options.index(correct_text)
    return shuffled_options, correct_index


def finalize_binary_options(rng, option_a: str, option_b: str, correct_text: str):
    """Same contract as finalize_options() but for a true 2-option (head-to-
    head comparison) package -- no distractor pool at all, both options are
    real named entities. package_contract.py's _validate_guess_question()
    only ever requires len(options) >= 2, so this is a fully valid "guess"
    package, not a different mechanic."""
    options = [option_a, option_b]
    order = list(range(2))
    rng.shuffle(order)
    shuffled_options = [options[i] for i in order]
    correct_index = shuffled_options.index(correct_text)
    return shuffled_options, correct_index


def write_quiz_js(path: Path, global_name: str, header_lines: list[str], records: list[dict]) -> None:
    clean = [{k: r[k] for k in CONTRACT_KEY_ORDER} for r in records]
    header = "\n".join(header_lines) + "\n" + f"window.{global_name} = "
    body = json.dumps(clean, indent=2, ensure_ascii=False)
    path.write_text(header + body + ";\n", encoding="utf-8")
