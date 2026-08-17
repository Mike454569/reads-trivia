"""Reliability-design Phase 1 -- the 5-way drift test.

Confirms five things agree, on every CI run: capability_catalog rows,
generated schema.py allowlists, the Anthropic prompt's enum lines + body
mentions, registry.py entries, and real adapter-module importability. This
is the test that would have caught both real staleness incidents found
earlier in this project (Task A's stale Anthropic prompt, a later gap where
it was stale by 11 capabilities) automatically, rather than by manual audit.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _catalog_triples():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    try:
        rows = catalog.list_capabilities(c)
    finally:
        c.close()
    return {(r["mechanic"], r["domain"], r["relationship_predicate"]) for r in rows}


def test_catalog_and_registry_have_identical_triples():
    from tools.director_v02 import registry

    catalog_triples = _catalog_triples()
    registry_triples = set(registry.CAPABILITY_REGISTRY.keys())
    assert catalog_triples == registry_triples, (
        f"catalog/registry drift -- in catalog only: {catalog_triples - registry_triples}, "
        f"in registry only: {registry_triples - catalog_triples}"
    )


def test_catalog_and_schema_allowlists_have_identical_domains_and_predicates():
    from tools.director_v02 import generate_schema_and_prompt as gen
    from tools.director_v02 import schema as schema_mod

    domains, predicates = gen.catalog_domains_and_predicates()
    assert domains == schema_mod.ALLOWED_DOMAINS
    assert predicates == schema_mod.ALLOWED_PREDICATES


def test_schema_generator_is_idempotent_against_current_file():
    """Running the generator again right now must report no change -- if it
    does, schema.py has drifted from the catalog and needs regenerating."""
    from tools.director_v02 import generate_schema_and_prompt as gen

    result = gen.generate_schema_allowlists(write=False)
    assert result["changed"] is False, "schema.py's generated block is stale -- re-run the generator"


def test_anthropic_prompt_matches_catalog():
    from tools.director_v02 import generate_schema_and_prompt as gen

    result = gen.verify_anthropic_prompt()
    assert result["ok"], result


def test_every_catalog_row_has_exactly_one_registry_entry_and_an_importable_adapter():
    from tools.director_v02 import catalog

    c = engine_bootstrap.connect()
    try:
        rows = catalog.list_capabilities(c)
    finally:
        c.close()

    failures = []
    for row in rows:
        result = catalog.verify_registry_consistency(row["capability_id"])
        if not result["ok"]:
            failures.append((row["capability_id"], result["reason"]))
    assert not failures, f"registry/adapter drift: {failures}"
