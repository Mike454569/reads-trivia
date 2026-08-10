"""Shared human-review markdown skeleton.

The per-question block shape (ID/question header, category, difficulty,
options-with-correct-marker) was identical across all three original
`generate_human_review*.py` scripts. Domain-specific context lines (draft
year/team; QB/season/team; season/team/outcome) are supplied by the caller
via context_fn, keeping football-domain interpretation out of this module.
"""
from __future__ import annotations


def render_human_review_markdown(*, title: str, intro: str, summary_lines: list[str], records: list[dict], context_fn) -> str:
    lines = [f"# {title}", "", intro, "", "## Summary", ""]
    lines.extend(summary_lines)
    lines.append("")
    lines.append("---")
    lines.append("")
    for r in records:
        lines.append(f"## #{r['id']} -- {r['question']}")
        lines.append("")
        lines.append(f"- **Category:** {r['category']}")
        lines.append(f"- **Difficulty:** {r['difficulty']}")
        lines.append("- **Options:**")
        for i, opt in enumerate(r["options"]):
            marker = " **<- CORRECT**" if i == r["correctIndex"] else ""
            lines.append(f"  {i}. {opt}{marker}")
        lines.extend(context_fn(r))
        lines.append("")
    return "\n".join(lines) + "\n"
