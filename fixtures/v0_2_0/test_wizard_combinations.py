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

    def pick_option(self, prompt, options, default_key=None):
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
    def section_title(self, *a, **kw): pass
    def banner(self, *a, **kw): pass
    def progress_ticker(self, *a, **kw): pass
    def print_blank(self, *a, **kw): pass
    def subrule(self, *a, **kw): pass

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

# Keys are (substring of the prompt) -> answer.
# We rely on the wizard's prompts being stable + readable English.
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
    # step 11 - refine tier
    "refine tier": "normal",
    "Refine tier": "normal",
    "tier": "normal",
    # step 12 - card structure
    "card structure": "standard",
    "Card structure": "standard",
    # step 14 - taxonomy
    "taxonomy seed": "minimal",
    "Taxonomy": "minimal",
    # step 15 - budget
    "Daily budget": 20.0,
    "daily budget": 20.0,
    # step 16 - confirm
    "Save the config": True,
    "Confirm": True,
    "ready to save": True,
    "save and exit": True,
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
