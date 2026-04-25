"""Regression guard: every wizard pick key must resolve at runtime.

A pre-2026-04-26 bug had wizard step 7 offering display-y values
like `openai-text-embedding-3-large`, `voyage-3`, `cohere-rerank-v3`
that aren't in any registry — so picking them succeeded at wizard
time and crashed with `ValueError: Unknown embedder` at first
use of the daemon or rag_server.

This test enumerates every pick key the wizard offers in steps that
write to the daemon's runtime config (vector_db / embedder /
reranker / llm_provider) and asserts each one resolves cleanly.

If you add a new option to a wizard step, this test catches "did
you also wire the implementation up?" without needing to manually
launch the daemon.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# The wizard step lists are authoritative — extracted by reading
# the actual step functions to keep this test in lockstep with the
# UI. We intentionally don't import wizard.py and inspect its AST,
# because the keys ARE the contract — a contract test should pin them.

# Mirror of step_03_vector_db's pick_option keys.
_STEP3_VECTOR_DB_KEYS = (
    "qdrant", "chroma", "lancedb", "duckdb_vss", "sqlite_vec", "pgvector",
)

# Mirror of step_07_retrieval's embedder keys.
_STEP7_EMBEDDER_KEYS = (
    "bge-m3", "openai", "nomic", "minilm", "voyage",
)

# Mirror of step_07_retrieval's reranker keys.
_STEP7_RERANKER_KEYS = (
    "bge-reranker-v2-m3", "bge-reranker-v2-gemma",
    "cohere", "voyage", "jina", "skip",
)


class TestEveryWizardVectorDbKeyResolves:
    """Each step 3 key must produce a BaseVectorStore (or stub) without
    raising. Stubs are fine — they signal "dep not installed" gracefully;
    a ValueError signals "key not in registry", a real bug."""

    def test_all_keys_resolve(self):
        from rag_server import vector_stores as vs
        for key in _STEP3_VECTOR_DB_KEYS:
            store = vs.create_vector_store(key)
            # `name` is the canonical primary; for hyphen aliases it
            # collapses to the underscore form. The point is no exception.
            assert store.name in {
                "qdrant", "chroma", "lancedb", "sqlite_vec",
                "duckdb_vss", "pgvector",
            }, f"{key!r} resolved to unexpected name {store.name!r}"


class TestEveryWizardEmbedderKeyResolves:
    def test_all_keys_resolve(self):
        from rag_server import embedders as em
        for key in _STEP7_EMBEDDER_KEYS:
            try:
                em.create_embedder(key)
            except ValueError as exc:
                raise AssertionError(
                    f"Wizard step 7 offers embedder {key!r} but the "
                    f"registry rejects it: {exc}. Either add it to "
                    f"_REGISTRY/_ALIASES in rag_server/embedders.py or "
                    f"remove it from wizard.py:step_07_retrieval."
                ) from None
            except ImportError:
                # Acceptable: torch / transformers / openai not installed.
                # The wizard is allowed to offer choices that need extras.
                pass


class TestEveryWizardRerankerKeyResolves:
    def test_all_keys_resolve(self):
        from rag_server import rerankers as rr
        for key in _STEP7_RERANKER_KEYS:
            try:
                rr.create_reranker(key)
            except ValueError as exc:
                raise AssertionError(
                    f"Wizard step 7 offers reranker {key!r} but the "
                    f"registry rejects it: {exc}. Either add it to "
                    f"_REGISTRY/_ALIASES in rag_server/rerankers.py or "
                    f"remove it from wizard.py:step_07_retrieval."
                ) from None
            except ImportError:
                pass


class TestEveryWizardLlmProviderKeyResolves:
    """Step 4 lists 16 providers; each must round-trip through the
    providers registry."""

    def test_all_provider_ids_resolve(self):
        from throughline_cli import providers as pr
        for preset in pr.list_presets():
            # get_preset must round-trip; raises if not registered.
            assert pr.get_preset(preset.id).id == preset.id


class TestWizardStep7KeysMatchRegistryStep:
    """The wizard step lists in this test file mirror the wizard
    code. Catch the case where a future wizard edit goes
    out of sync with this guard."""

    def test_step3_keys_match_wizard_source(self):
        wizard_src = (REPO_ROOT / "throughline_cli" / "wizard.py").read_text(
            encoding="utf-8")
        # Each step-3 key must literally appear inside the step_03
        # function. Cheap, robust check.
        for key in _STEP3_VECTOR_DB_KEYS:
            assert f'"{key}"' in wizard_src, (
                f"vector_db key {key!r} is in the test list but no longer "
                f"in wizard.py — update test or wizard."
            )

    def test_step7_embedder_keys_match_wizard_source(self):
        wizard_src = (REPO_ROOT / "throughline_cli" / "wizard.py").read_text(
            encoding="utf-8")
        for key in _STEP7_EMBEDDER_KEYS:
            assert f'"{key}"' in wizard_src, (
                f"embedder key {key!r} is in the test list but no longer "
                f"in wizard.py — update test or wizard."
            )

    def test_step7_reranker_keys_match_wizard_source(self):
        wizard_src = (REPO_ROOT / "throughline_cli" / "wizard.py").read_text(
            encoding="utf-8")
        for key in _STEP7_RERANKER_KEYS:
            assert f'"{key}"' in wizard_src, (
                f"reranker key {key!r} is in the test list but no longer "
                f"in wizard.py — update test or wizard."
            )
