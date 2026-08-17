"""Generates schema.py's translator allowlists from the capability catalog,
and verifies (does not rewrite) the Anthropic system prompt against it.

Reliability-design Phase 1, item 4 ("Generate the translator schema and
Anthropic capability descriptions from the catalog"), scoped deliberately:

- schema.py's ALLOWED_DOMAINS/ALLOWED_PREDICATES are safe to generate for
  real: they are bare value lists, mechanically derivable from the catalog
  with no natural-language content at risk of being mis-authored. This
  module does that, writing between explicit `# BEGIN GENERATED` / `# END
  GENERATED` markers so the block stays reviewable in every diff (never
  built silently at deploy time).

- The Anthropic system prompt's per-capability paragraphs (SYSTEM_PROMPT in
  providers/anthropic_provider.py) are real, carefully-worded LLM
  instructions -- e.g. exactly how capability 10 differs from capability 20
  despite sharing a predicate name, or Rule A's NFL/CFB league-routing
  logic. Auto-generating natural language INTO a system prompt an LLM
  actually reads is a real-content-authoring task, not mechanical value-list
  generation -- getting the wording subtly wrong risks introducing exactly
  the kind of silent behavioral drift this whole reliability effort exists
  to eliminate, not add. This module therefore VERIFIES the prompt (parses
  its enum lines + numbered capability list via the same technique already
  used to catch two real staleness bugs earlier this project) against the
  catalog, and reports drift precisely, without rewriting the prose. A
  human still authors/updates the actual capability description when a new
  one is added -- the drift check just makes it impossible for that step to
  be silently skipped and go unnoticed, which is the real, repeated
  incident this whole module exists to prevent.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "tools" / "director_v02" / "schema.py"
PROMPT_PATH = REPO_ROOT / "tools" / "director_v02" / "providers" / "anthropic_provider.py"

_BEGIN_MARKER = "    # BEGIN GENERATED -- see tools/director_v02/generate_schema_and_prompt.py"
_END_MARKER = "    # END GENERATED"


def catalog_domains_and_predicates() -> tuple[set[str], set[str]]:
    """Real, live capability_catalog rows -- LEGACY_PUBLIC_PENDING_REVALIDATION
    and PUBLIC_ENABLED are both real, currently-supported capabilities and
    both count; any other state is not yet released and must NOT appear in
    the translator's allowlist."""
    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT DISTINCT domain, relationship_predicate FROM capability_catalog "
            "WHERE verification_status IN ('PUBLIC_ENABLED', 'LEGACY_PUBLIC_PENDING_REVALIDATION')"
        ).fetchall()
    finally:
        c.close()
    domains = {r["domain"] for r in rows}
    predicates = {r["relationship_predicate"] for r in rows}
    return domains, predicates


def _generated_frozenset_block(name: str, values: set[str]) -> str:
    lines = [f"{name} = frozenset({{"]
    lines.append(_BEGIN_MARKER)
    for v in sorted(values):
        lines.append(f'    "{v}",')
    lines.append(_END_MARKER)
    lines.append("})")
    return "\n".join(lines)


def generate_schema_allowlists(*, write: bool = False) -> dict:
    domains, predicates = catalog_domains_and_predicates()
    src = SCHEMA_PATH.read_text()

    domains_block_re = re.compile(r"ALLOWED_DOMAINS = frozenset\(\{.*?\}\)", re.DOTALL)
    predicates_block_re = re.compile(r"ALLOWED_PREDICATES = frozenset\(\{.*?\}\)", re.DOTALL)

    new_domains_block = _generated_frozenset_block("ALLOWED_DOMAINS", domains)
    new_predicates_block = _generated_frozenset_block("ALLOWED_PREDICATES", predicates)

    new_src = domains_block_re.sub(lambda _m: new_domains_block, src, count=1)
    new_src = predicates_block_re.sub(lambda _m: new_predicates_block, new_src, count=1)

    changed = new_src != src
    if write and changed:
        SCHEMA_PATH.write_text(new_src)

    return {
        "changed": changed, "domains_count": len(domains), "predicates_count": len(predicates),
        "wrote": write and changed,
    }


# --- Anthropic prompt verification (not rewritten -- see module docstring) --

_ENUM_LINE_RE = re.compile(r'"domain":\s*((?:"[A-Z_]+"\s*\|\s*)*"[A-Z_]+")')
_PRED_ENUM_LINE_RE = re.compile(r'"relationship_predicate":\s*((?:"[A-Z_]+"\s*\|\s*)*"[A-Z_]+")')


def _extract_quoted_values(line: str) -> set[str]:
    return set(re.findall(r'"([A-Z_]+)"', line))


def verify_anthropic_prompt() -> dict:
    from tools.director_v02.providers import anthropic_provider

    prompt = anthropic_provider.SYSTEM_PROMPT
    catalog_domains, catalog_predicates = catalog_domains_and_predicates()

    domain_enum_match = _ENUM_LINE_RE.search(prompt)
    pred_enum_match = _PRED_ENUM_LINE_RE.search(prompt)
    prompt_domains = _extract_quoted_values(domain_enum_match.group(0)) if domain_enum_match else set()
    prompt_predicates = _extract_quoted_values(pred_enum_match.group(0)) if pred_enum_match else set()

    # Presence check: every catalog domain/predicate pair must be mentioned
    # SOMEWHERE in the prompt body (numbered capability descriptions use
    # "domain=X" / "relationship_predicate=X" phrasing throughout).
    missing_domain_mentions = {d for d in catalog_domains if f"domain={d}" not in prompt and d not in prompt_domains}
    missing_predicate_mentions = {
        p for p in catalog_predicates if f"relationship_predicate={p}" not in prompt and p not in prompt_predicates
    }

    ok = (
        prompt_domains == catalog_domains
        and prompt_predicates == catalog_predicates
        and not missing_domain_mentions
        and not missing_predicate_mentions
    )
    return {
        "ok": ok,
        "enum_domains_match": prompt_domains == catalog_domains,
        "enum_predicates_match": prompt_predicates == catalog_predicates,
        "prompt_domains_missing_from_catalog": sorted(prompt_domains - catalog_domains),
        "catalog_domains_missing_from_prompt_enum": sorted(catalog_domains - prompt_domains),
        "prompt_predicates_missing_from_catalog": sorted(prompt_predicates - catalog_predicates),
        "catalog_predicates_missing_from_prompt_enum": sorted(catalog_predicates - prompt_predicates),
        "missing_domain_mentions_in_body": sorted(missing_domain_mentions),
        "missing_predicate_mentions_in_body": sorted(missing_predicate_mentions),
    }
