"""Combinatorial integration test for the wizard.

The user asked: "不是所有人都default下去，不同组合的可能性太多了"
("not everyone picks defaults; the combination space is huge").

This test runs the wizard end-to-end with a script of non-default
picks for the highest-leverage axes (mission × privacy × vector_db
× provider × import × tier). For each combination it asserts:

1. The wizard completes without raising.
2. The resulting `config.toml` validates clean (`config.validate()`
   returns no issues — no enum drift, no broken keys).
3. The pluggable backends listed in config can be instantiated
   through `create_vector_store / create_embedder / create_reranker`
   without `ValueError: Unknown ...`.

The test bypasses real I/O via a mocked ui module that returns
scripted answers and swallows display calls. No real LLM call,
no network, no Qdrant, no Obsidian.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# Wizard mock harness
# ============================================================

class _ScriptedUI:
    """Mock for the wizard's ui module. pick_option/ask_yes_no/
    ask_text return the scripted answer for that key; everything
    else is a no-op.

    The scripted dict maps `(step_number, prompt_key) -> answer`.
    For free-form prompts (ask_text), the prompt label IS the key.
    For pick_option, we match by the question's leading words —
    the wizard's prompts are stable.
    """

    def __init__(self, answers: Dict[str, Any]):
        self.answers = answers
        self.captured_msgs: list = []

    def _resolve(self, prompt: str, default: Any = None) -> Any:
        for key, val in self.answers.items():
            if key.lower() in prompt.lower():
                return val
        return default

    def pick_option(self, prompt, options, default_key=None,
                     show_back=False):
        # show_back is ignored by the test harness — combinatorial
        # tests never want to exercise the back-navigation flow;
        # they go forward only. Real back-nav coverage lives in
        # test_wizard_back_navigation.py.
        ans = self._resolve(prompt, default_key)
        # Validate the answer is a known option key.
        keys = [k for k, _, _ in options]
        if ans not in keys:
            raise AssertionError(
                f"Test answer {ans!r} not in pick_option keys {keys} "
                f"for prompt {prompt!r}")
        return ans

    def ask_yes_no(self, prompt, default=True):
        return self._resolve(prompt, default)

    def ask_text(self, prompt, default=""):
        return self._resolve(prompt, default)

    def ask_int(self, prompt, default=0):
        return self._resolve(prompt, default)

    def ask_float(self, prompt, default=0.0):
        return self._resolve(prompt, default)

    # All decoration calls are no-ops.
    def step_header(self, *a, **kw): pass
    def intro(self, *a, **kw): pass
    def info_line(self, msg, *a, **kw): self.captured_msgs.append(str(msg))
    def warn_box(self, *a, **kw): pass
    def panel_example(self, *a, **kw): pass
    def kv_row(self, *a, **kw): pass
    def summary_tree(self, *a, **kw): pass
    def section_title(self, *a, **kw): pass
    def banner(self, *a, **kw): pass
    def progress_ticker(self, *a, **kw): pass
    def print_blank(self, *a, **kw): pass
    def subrule(self, *a, **kw): pass

    def status(self, message, *a, **kw):
        # Context manager that just emits the message and exits.
        captured = self.captured_msgs

        class _Null:
            def __enter__(self_inner):
                captured.append(str(message))
                return self_inner

            def __exit__(self_inner, *exc):
                return False

            def update(self_inner, m):
                captured.append(str(m))

        return _Null()

    class _Console:
        def print(self, *a, **kw): pass

    @property
    def console(self):
        return self._Console()


def _run_with_script(tmp_path, monkeypatch, answers: Dict[str, Any]):
    """Drive the wizard end-to-end with the scripted answers and
    return the resulting WizardConfig. Each test isolates its own
    config dir so they can run in parallel."""
    monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / ".throughline"))

    # Reload the wizard module so it picks up our mocked ui object.
    for mod in list(sys.modules):
        if mod in ("throughline_cli.wizard", "throughline_cli.config"):
            del sys.modules[mod]

    from throughline_cli import wizard as wiz
    from throughline_cli import config as cfg_mod

    scripted = _ScriptedUI(answers)
    monkeypatch.setattr(wiz, "ui", scripted)
    # Step 13 (preview) calls llm.call_chat — short-circuit by
    # making import_source = "none" in every test scenario, so the
    # preview step early-exits with "no import source".
    # Step 10 same — no import → skipped.
    cfg = wiz.run_wizard(cfg=cfg_mod.WizardConfig())
    return cfg, scripted


# ============================================================
# Combination matrix
# ============================================================

# Keys are the (substring of the actual prompt the wizard emits) ->
# answer. Substring matched lowercase; the matcher returns the first
# matching entry, so list more-specific keys first.
_BASE_ANSWERS: Dict[str, Any] = {
    # step 2 - mission (interactive subrule + numbered text picker)
    "mission": "full",
    # step 3 - "Pick a vector DB backend"
    "vector DB": "qdrant",
    # step 4 - "Pick an LLM provider"
    "LLM provider": "openrouter",
    # step 5 - "Pick a model"
    "Pick a model": "anthropic/claude-sonnet-4.6",
    "Model ID": "anthropic/claude-sonnet-4.6",  # for generic fallback
    # step 6 - "How much of the pipeline may hit the cloud"
    "pipeline may hit": "hybrid",
    # step 7
    "Embedder": "bge-m3",
    "Reranker": "bge-reranker-v2-m3",
    # step 8 - prompt family override prompt
    "Accept": True,
    "Override prompt family": "claude",
    # step 9 - import source
    "existing LLM chat history to import": "none",
    # step 11 - "How deep should the refiner think on each conversation?"
    "How deep": "normal",
    # step 12 - "Pick a card shape:"
    "card shape": "standard",
    # step 14 - "How should throughline pick card folders?"
    "card folders": "minimal",
    # step 15 - "Daily budget (USD)" (ask_text)
    "Daily budget": "20.0",
    # step 16 - confirm
    "Save the config": True,
    "Confirm": True,
    "ready to save": True,
    "save and exit": True,
    # step 4's hard-block on unset API key (added 2026-04-26): the
    # wizard now warns + asks "Continue anyway?" when the chosen
    # provider's env var isn't set. In tests we don't export real
    # keys, so the warning ALWAYS fires — answer 'yes' to keep
    # the wizard moving.
    "Continue anyway": True,
}


def _combo(**overrides) -> Dict[str, Any]:
    """Create an answer dict from base + overrides."""
    out = dict(_BASE_ANSWERS)
    out.update(overrides)
    return out


# ============================================================
# Tests
# ============================================================

class TestWizardCombinations:
    """Each combination produces a config.toml that:
      1. The wizard wrote without raising.
      2. config.validate() returns no issues for.
      3. Whose vector_db / embedder / reranker resolve through
         their respective registries."""

    def _verify_clean(self, tmp_path, cfg):
        """Reusable assertions across all combinations."""
        from throughline_cli import config as cfg_mod
        from rag_server import vector_stores as vs
        from rag_server import embedders as em
        from rag_server import rerankers as rr

        # 1. The wizard saved a parseable config.
        config_path = tmp_path / ".throughline" / "config.toml"
        assert config_path.exists(), "wizard did not write config.toml"

        # 2. Schema validates clean.
        import tomllib
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
        issues = cfg_mod.validate(raw)
        assert issues == [], (
            "config.validate() failed: " +
            "; ".join(f"{i.kind}:{i.key}={i.detail}" for i in issues))

        # 3. The pluggable backend choices resolve through their
        # registries. Notes-only writes "none" for all three —
        # vector_db routes via _ALIASES, embedder/reranker stay as
        # "none" string in config but the rag_server isn't actually
        # used in that mission. So skip the embedder/reranker check
        # if mission is notes_only.
        store = vs.create_vector_store(cfg.vector_db)
        assert store is not None
        if cfg.mission != "notes_only":
            try:
                em.create_embedder(cfg.embedder)
            except (ImportError, ValueError) as e:
                # ImportError is fine (torch / openai not installed in
                # CI); ValueError is the bug we're guarding.
                if isinstance(e, ValueError):
                    raise
            try:
                rr.create_reranker(cfg.reranker)
            except (ImportError, ValueError) as e:
                if isinstance(e, ValueError):
                    raise

    # -------- mission axis --------

    def test_full_mission_qdrant_hybrid(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo())
        assert cfg.mission == "full"
        self._verify_clean(tmp_path, cfg)

    def test_rag_only_mission(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch,
                                    _combo(mission="rag_only"))
        assert cfg.mission == "rag_only"
        # rag_only mission forces card_structure
        assert cfg.card_structure == "rag_optimized"
        assert cfg.refine_tier == "skim"
        self._verify_clean(tmp_path, cfg)

    def test_notes_only_mission_skips_rag_steps(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch,
                                    _combo(mission="notes_only"))
        assert cfg.mission == "notes_only"
        # vector_db / embedder / reranker auto-set to "none"
        assert cfg.vector_db == "none"
        assert cfg.embedder == "none"
        assert cfg.reranker == "none"
        self._verify_clean(tmp_path, cfg)

    # -------- vector_db × dep-availability --------

    def test_lancedb_choice(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch,
                                    _combo(**{"vector DB": "lancedb"}))
        assert cfg.vector_db == "lancedb"
        self._verify_clean(tmp_path, cfg)

    def test_sqlite_vec_choice(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch,
                                    _combo(**{"vector DB": "sqlite_vec"}))
        assert cfg.vector_db == "sqlite_vec"
        self._verify_clean(tmp_path, cfg)

    def test_duckdb_vss_choice(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch,
                                    _combo(**{"vector DB": "duckdb_vss"}))
        assert cfg.vector_db == "duckdb_vss"
        self._verify_clean(tmp_path, cfg)

    def test_pgvector_choice(self, tmp_path, monkeypatch):
        cfg, scripted = _run_with_script(tmp_path, monkeypatch,
                                            _combo(**{"vector DB": "pgvector"}))
        assert cfg.vector_db == "pgvector"
        self._verify_clean(tmp_path, cfg)
        # Step 3 should have warned about PGVECTOR_DSN being unset.
        joined = "\n".join(scripted.captured_msgs)
        assert "PGVECTOR_DSN" in joined or "psycopg" in joined.lower()

    def test_chroma_choice(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch,
                                    _combo(**{"vector DB": "chroma"}))
        assert cfg.vector_db == "chroma"
        self._verify_clean(tmp_path, cfg)

    # -------- embedder × reranker non-default --------

    def test_openai_embedder_cohere_reranker(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
            Embedder="openai", Reranker="cohere",
        ))
        assert cfg.embedder == "openai"
        assert cfg.reranker == "cohere"
        self._verify_clean(tmp_path, cfg)

    def test_voyage_jina_combo(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
            Embedder="voyage", Reranker="jina",
        ))
        assert cfg.embedder == "voyage"
        assert cfg.reranker == "jina"
        self._verify_clean(tmp_path, cfg)

    def test_minimal_embedder_skip_reranker(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
            Embedder="minilm", Reranker="skip",
        ))
        assert cfg.embedder == "minilm"
        assert cfg.reranker == "skip"
        self._verify_clean(tmp_path, cfg)

    # -------- privacy × provider conflict --------

    def test_local_only_with_ollama_no_warning(self, tmp_path, monkeypatch):
        cfg, scripted = _run_with_script(tmp_path, monkeypatch, _combo(
            **{"pipeline may hit": "local_only",
                "LLM provider":     "ollama",
                "Pick a model":     "llama3.3:70b"}
        ))
        assert cfg.privacy == "local_only"
        assert cfg.llm_provider == "ollama"
        joined = "\n".join(scripted.captured_msgs)
        # No conflict warning should have fired.
        assert "Conflict" not in joined
        self._verify_clean(tmp_path, cfg)

    def test_local_only_with_openai_warns(self, tmp_path, monkeypatch):
        cfg, scripted = _run_with_script(tmp_path, monkeypatch, _combo(
            **{"pipeline may hit": "local_only",
                "LLM provider":     "openai",
                "Pick a model":     "gpt-5-mini"}
        ))
        assert cfg.privacy == "local_only"
        # Conflict warning fired (the wizard still saved; we don't
        # block, just inform).
        joined = "\n".join(scripted.captured_msgs)
        assert ("Conflict" in joined or "local_only" in joined.lower()), (
            f"expected conflict warning, got: {joined[:500]}")
        self._verify_clean(tmp_path, cfg)

    # -------- full mode + cloud_max --------

    def test_cloud_max_full_install(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
            **{"pipeline may hit": "cloud_max",
                "Embedder":          "openai",
                "Reranker":          "cohere"}
        ))
        assert cfg.privacy == "cloud_max"
        self._verify_clean(tmp_path, cfg)

    # -------- China-market provider --------

    def test_siliconflow_provider(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
            **{"LLM provider": "siliconflow",
                "Pick a model": "Qwen/Qwen2.5-72B-Instruct"}
        ))
        assert cfg.llm_provider == "siliconflow"
        self._verify_clean(tmp_path, cfg)

    def test_anthropic_direct_provider(self, tmp_path, monkeypatch):
        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
            **{"LLM provider": "anthropic",
                "Pick a model": "claude-sonnet-4-5-20250929"}
        ))
        assert cfg.llm_provider == "anthropic"
        # prompt_family auto-derives to claude
        assert cfg.prompt_family == "claude"
        self._verify_clean(tmp_path, cfg)


# ============================================================
# Exhaustive: every LLM provider with its default model
# ============================================================

import pytest as _pytest
from throughline_cli.providers import list_presets as _list_presets


@_pytest.fixture(scope="module")
def all_provider_ids():
    return [p.id for p in _list_presets()]


@_pytest.mark.parametrize("provider_id",
                            [p.id for p in _list_presets()])
class TestEveryProviderDefaultModel:
    """Exhaustive: every one of the 16 LLM providers must wizard
    cleanly with its declared default model. Catches the
    wizard.py-vs-providers.py drift class that broke step 7
    (different shape, same root cause)."""

    def _provider_preset(self, provider_id):
        from throughline_cli.providers import get_preset
        return get_preset(provider_id)

    def test_default_model_round_trip(self, tmp_path, monkeypatch,
                                        provider_id):
        preset = self._provider_preset(provider_id)
        # Generic provider has no preset model list; user supplies.
        if not preset.models:
            model = "custom-model-id"
        else:
            model = preset.models[0][0]

        cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
            **{"LLM provider":  provider_id,
                "Pick a model":  model,
                "Model ID":      model,  # for generic free-form input
                }
        ))
        assert cfg.llm_provider == provider_id
        assert cfg.llm_provider_id == model
        # The config must validate clean — including the new dynamic
        # llm_provider validation (added in 678532c).
        from throughline_cli import config as cfg_mod
        import tomllib
        config_path = tmp_path / ".throughline" / "config.toml"
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
        issues = cfg_mod.validate(raw)
        assert issues == [], (
            f"provider {provider_id!r} produced config issues: " +
            "; ".join(f"{i.kind}:{i.key}" for i in issues))


@_pytest.mark.parametrize("provider_id",
                            [p.id for p in _list_presets() if p.models])
def test_provider_prompt_family_auto_derives(tmp_path, monkeypatch,
                                                provider_id):
    """prompt_family auto-derivation in step 5 (lines 232-240 of
    wizard.py). Each provider's default model must derive a valid
    family — claude / gpt / gemini / generic."""
    from throughline_cli.providers import get_preset
    preset = get_preset(provider_id)
    model = preset.models[0][0]
    cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
        **{"LLM provider":  provider_id,
            "Pick a model":  model,
            "Model ID":      model,
            }
    ))
    assert cfg.prompt_family in {"claude", "gpt", "gemini", "generic"}, (
        f"provider {provider_id!r} model {model!r} derived "
        f"unrecognized prompt_family {cfg.prompt_family!r}")


# ============================================================
# Exhaustive: every embedder × reranker combination
# ============================================================

# Mirror of step_07_retrieval keys (covered by the sibling
# `test_wizard_keys_resolve.py`; this expands to every PAIR).
_ALL_EMBEDDERS = ("bge-m3", "openai", "nomic", "minilm", "voyage")
_ALL_RERANKERS = ("bge-reranker-v2-m3", "bge-reranker-v2-gemma",
                   "cohere", "voyage", "jina", "skip")


@_pytest.mark.parametrize("embedder", _ALL_EMBEDDERS)
@_pytest.mark.parametrize("reranker", _ALL_RERANKERS)
def test_every_embedder_reranker_pair(tmp_path, monkeypatch,
                                          embedder, reranker):
    """5 × 6 = 30 pairs. Each must produce a config that
    (a) wizards cleanly, (b) validates, (c) resolves both
    backends through their registries without ValueError."""
    cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
        Embedder=embedder, Reranker=reranker,
    ))
    assert cfg.embedder == embedder
    assert cfg.reranker == reranker

    # Validate config.
    from throughline_cli import config as cfg_mod
    import tomllib
    raw = tomllib.loads(
        (tmp_path / ".throughline" / "config.toml").read_text(
            encoding="utf-8"))
    assert cfg_mod.validate(raw) == [], (
        f"pair ({embedder}, {reranker}) failed validation")

    # Resolve through registries — ImportError is OK (extras not
    # installed in CI), ValueError is the registry-drift bug.
    from rag_server import embedders as em
    from rag_server import rerankers as rr
    try:
        em.create_embedder(embedder)
    except ImportError:
        pass
    except ValueError as e:
        raise AssertionError(
            f"embedder {embedder!r} not in registry: {e}")
    try:
        rr.create_reranker(reranker)
    except ImportError:
        pass
    except ValueError as e:
        raise AssertionError(
            f"reranker {reranker!r} not in registry: {e}")


# ============================================================
# Exhaustive: every refine_tier × card_structure combination
# ============================================================

_ALL_TIERS = ("skim", "normal", "deep")
# `rag_optimized` is FORCED by mission=rag_only (step 12 returns
# SKIPPED) — not user-pickable when mission=full. Tested separately.
_ALL_CARD_STRUCTURES = ("compact", "standard", "detailed")


@_pytest.mark.parametrize("tier", _ALL_TIERS)
@_pytest.mark.parametrize("structure", _ALL_CARD_STRUCTURES)
def test_every_tier_structure_pair(tmp_path, monkeypatch,
                                      tier, structure):
    """3 × 3 = 9 user-pickable pairs. Each writes config + validates."""
    cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
        **{"How deep":   tier,
            "card shape": structure}
    ))
    assert cfg.refine_tier == tier
    assert cfg.card_structure == structure

    from throughline_cli import config as cfg_mod
    import tomllib
    raw = tomllib.loads(
        (tmp_path / ".throughline" / "config.toml").read_text(
            encoding="utf-8"))
    assert cfg_mod.validate(raw) == []


def test_rag_only_forces_rag_optimized_card_structure(tmp_path, monkeypatch):
    """The 4th card structure value, `rag_optimized`, is reachable
    only via the mission=rag_only forced-path (step 12 SKIPPED)."""
    cfg, _ = _run_with_script(tmp_path, monkeypatch,
                                _combo(mission="rag_only"))
    assert cfg.card_structure == "rag_optimized"
    # Same validate sweep:
    from throughline_cli import config as cfg_mod
    import tomllib
    raw = tomllib.loads(
        (tmp_path / ".throughline" / "config.toml").read_text(
            encoding="utf-8"))
    assert cfg_mod.validate(raw) == []


# ============================================================
# Exhaustive: every taxonomy_source × privacy combination
# ============================================================

_ALL_TAXONOMY = ("minimal", "derive_from_vault", "derive_from_imports",
                   "jd", "para", "zettel")
_ALL_PRIVACY = ("local_only", "hybrid", "cloud_max")


@_pytest.mark.parametrize("taxonomy", _ALL_TAXONOMY)
@_pytest.mark.parametrize("privacy", _ALL_PRIVACY)
def test_every_taxonomy_privacy_pair(tmp_path, monkeypatch,
                                          taxonomy, privacy):
    """6 × 3 = 18 pairs. Catches taxonomy_source values that aren't
    in the WizardConfig schema (would land in config.toml as a typo
    and fail validate())."""
    # local_only privacy + cloud llm_provider would warn but not
    # fail; pick ollama for clean local-only path.
    provider = "ollama" if privacy == "local_only" else "openrouter"
    model = ("llama3.3:70b" if provider == "ollama"
             else "anthropic/claude-sonnet-4.6")

    cfg, _ = _run_with_script(tmp_path, monkeypatch, _combo(
        **{"card folders":      taxonomy,
            "pipeline may hit":  privacy,
            "LLM provider":      provider,
            "Pick a model":      model,
            }
    ))
    assert cfg.taxonomy_source == taxonomy
    assert cfg.privacy == privacy

    from throughline_cli import config as cfg_mod
    import tomllib
    raw = tomllib.loads(
        (tmp_path / ".throughline" / "config.toml").read_text(
            encoding="utf-8"))
    assert cfg_mod.validate(raw) == []
