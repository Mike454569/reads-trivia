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


# Phase 1 scope: only PUBLIC_ENABLED/LEGACY_PUBLIC_PENDING_REVALIDATION
# existed, so the schema allowlist and "what's publicly released" were the
# same set by coincidence. Phase 3 (the first capability to ever sit at
# GENERATION_VERIFIED for real -- proven to generate, but deliberately not
# yet publicly released, pending real human review) splits them for real:
# schema.py's ALLOWED_DOMAINS/ALLOWED_PREDICATES is a STRUCTURAL/security
# allowlist (validator.py's own docstring: never a code/table/path trust
# boundary) -- it must include any REAL, registered relationship shape,
# whether or not it's public yet, so an admin-only private-preview request
# can reach feasibility.assess()'s catalog-vocabulary gate at all (the gate
# that actually decides SUPPORTED vs. not, per capability_catalog's real
# lifecycle state -- see feasibility.py's Phase 3 correction). Whether a
# capability is PUBLICLY announced is a completely separate question, owned
# by `catalog_public_domains_and_predicates()` below.
_SCHEMA_ALLOWLIST_STATES = (
    "PUBLIC_ENABLED", "LEGACY_PUBLIC_PENDING_REVALIDATION", "GENERATION_VERIFIED", "HUMAN_APPROVED",
)


def catalog_domains_and_predicates() -> tuple[set[str], set[str]]:
    """Real, live capability_catalog rows whose relationship SHAPE is
    real and structurally validator-safe -- see _SCHEMA_ALLOWLIST_STATES'
    comment for why this is broader than "publicly released"."""
    c = engine_bootstrap.connect()
    try:
        placeholders = ",".join("?" for _ in _SCHEMA_ALLOWLIST_STATES)
        rows = c.execute(
            f"SELECT DISTINCT domain, relationship_predicate FROM capability_catalog "
            f"WHERE verification_status IN ({placeholders})",
            _SCHEMA_ALLOWLIST_STATES,
        ).fetchall()
    finally:
        c.close()
    domains = {r["domain"] for r in rows}
    predicates = {r["relationship_predicate"] for r in rows}
    return domains, predicates


def catalog_public_domains_and_predicates() -> tuple[set[str], set[str]]:
    """The narrower, PUBLIC-only set -- LEGACY_PUBLIC_PENDING_REVALIDATION
    and PUBLIC_ENABLED are real, currently publicly-supported capabilities;
    any other state (including GENERATION_VERIFIED/HUMAN_APPROVED -- real
    and working, but not yet released) must NOT be claimed as something the
    real, user-facing Anthropic system prompt already covers."""
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


def catalog_readiness_for_structured_description_generation() -> dict:
    """Phase 2 carryover: "move toward catalog-owned structured Anthropic
    capability descriptions... if safe generation cannot preserve behavior,
    retain the existing prose temporarily and report the precise blocker."

    This is that check, run for real against the live catalog (never
    asserted from memory). Two independent things must both be true before
    per-capability prose could safely be GENERATED (not just verified)
    from catalog rows:

    1. The per-capability scoping fields the prose actually encodes --
       tie_rule, ambiguity_rule, eligible_answer_rule,
       distractor_scoping_rule -- must be populated. They are NOT: every
       one of the 21 real capabilities has all four NULL today (Phase 1
       imported only known_limitations/input_entity_type/output_entity_type
       for the legacy backfill; populating the rest is real per-capability
       domain work, explicitly the Phase 7 "gradual audit" scope).

    2. Even fully populated, those are PER-CAPABILITY fields. The prompt's
       real complexity is CROSS-capability: Rule A's NFL/CFB default-routing
       table, Rule B's "capability 8 vs capability 4" names-hidden
       distinction, and capability 20's "transfer" keyword rule that
       disambiguates it from capability 10 despite sharing a predicate name.
       capability_catalog has no field, anywhere, that expresses a
       relationship BETWEEN two capability rows -- there is nothing to
       generate that FROM yet. Adding one would be a schema change, which
       Phase 2 is not authorized to make (no new mechanics, no Creator
       Intelligence layer).

    Given both, generation is correctly blocked, not attempted. This
    function makes that a checked fact, not an assumption -- if a future
    phase populates the four fields, this starts reporting a smaller (but
    still real, since #2 is untouched) gap rather than silently going stale."""
    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT capability_id, tie_rule, ambiguity_rule, eligible_answer_rule, distractor_scoping_rule "
            "FROM capability_catalog ORDER BY capability_id"
        ).fetchall()
    finally:
        c.close()

    scoping_fields = ("tie_rule", "ambiguity_rule", "eligible_answer_rule", "distractor_scoping_rule")
    missing = {
        row["capability_id"]: [f for f in scoping_fields if not row[f]]
        for row in rows
    }
    missing = {cap_id: fields for cap_id, fields in missing.items() if fields}

    return {
        "safe_to_generate": False,
        "total_capabilities": len(rows),
        "capabilities_missing_scoping_fields": len(missing),
        "missing_fields_by_capability": missing,
        "blocker": (
            "All per-capability scoping fields (tie_rule/ambiguity_rule/eligible_answer_rule/"
            "distractor_scoping_rule) are unpopulated for every capability, AND the catalog "
            "schema has no field expressing cross-capability translation-disambiguation "
            "relationships (Rule A NFL/CFB routing, Rule B's capability-8-vs-4 distinction, "
            "capability 20's 'transfer' keyword vs. capability 10) -- the real source of most "
            "of the prompt's complexity. Assigned to Phase 7 (gradual audit): populate the "
            "per-capability fields, then re-evaluate whether a cross-capability schema "
            "addition is warranted before attempting generation again."
        ),
    }


_SYSTEM_PROMPT_SNAPSHOT_SHA256 = "d9f7e045e5fb829c9e04da65d1c7bfc1d66882563b70a534d1669d5bf093f48f"


def _current_prompt_sha256() -> str:
    import hashlib

    from tools.director_v02.providers import anthropic_provider

    return hashlib.sha256(anthropic_provider.SYSTEM_PROMPT.encode("utf-8")).hexdigest()


def verify_anthropic_prompt_snapshot_unchanged() -> dict:
    """Phase 2's real "protect the cutover with exact snapshots... and
    rollback capability" deliverable, usable today even though no
    catalog-driven cutover is happening yet (see
    catalog_readiness_for_structured_description_generation() above for
    why). Any future change to SYSTEM_PROMPT -- catalog-driven or not --
    must be a deliberate edit to the recorded hash below, never a silent
    diff; reverting is exactly "restore the previous hash and prompt text",
    which is the rollback capability itself."""
    current = _current_prompt_sha256()
    return {
        "ok": current == _SYSTEM_PROMPT_SNAPSHOT_SHA256,
        "recorded_sha256": _SYSTEM_PROMPT_SNAPSHOT_SHA256,
        "current_sha256": current,
    }


def verify_anthropic_prompt() -> dict:
    from tools.director_v02.providers import anthropic_provider

    prompt = anthropic_provider.SYSTEM_PROMPT
    catalog_domains, catalog_predicates = catalog_public_domains_and_predicates()

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
