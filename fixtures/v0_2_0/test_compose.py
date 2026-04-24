"""Sanity checks for the bundled docker-compose + env template.

We don't actually `docker compose up` in CI (GitHub runners take
too long to pull images + the image itself), but we pin:
- The compose file is valid YAML.
- Expected services, volumes, env-file ref all present.
- .env.example.compose covers every provider env var the
  providers registry knows about.
- Dockerfile references the same env-var paths compose uses.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


class TestDockerComposeYaml:
    def _load(self):
        with (REPO_ROOT / "docker-compose.yml").open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_parses_as_yaml(self):
        data = self._load()
        assert "services" in data

    def test_expected_services(self):
        data = self._load()
        services = set(data["services"].keys())
        assert services == {"qdrant", "rag_server", "daemon"}

    def test_qdrant_healthcheck(self):
        data = self._load()
        qdrant = data["services"]["qdrant"]
        assert "healthcheck" in qdrant
        # /healthz is the documented Qdrant endpoint.
        cmd = str(qdrant["healthcheck"]["test"])
        assert "healthz" in cmd or "6333" in cmd

    def test_rag_server_depends_on_qdrant_healthy(self):
        data = self._load()
        rag = data["services"]["rag_server"]
        deps = rag["depends_on"]
        assert "qdrant" in deps
        assert deps["qdrant"]["condition"] == "service_healthy"

    def test_daemon_depends_on_both(self):
        data = self._load()
        d = data["services"]["daemon"]
        deps = d["depends_on"]
        assert "qdrant" in deps
        assert "rag_server" in deps

    def test_named_volumes(self):
        data = self._load()
        volumes = set(data["volumes"].keys())
        # Each named volume the services reference should be
        # declared at the top level.
        expected = {"qdrant_data", "vault", "raw", "state", "logs"}
        assert expected.issubset(volumes), f"missing volumes: {expected - volumes}"

    def test_qdrant_url_points_at_service_name(self):
        """The daemon should reach qdrant via Docker's internal DNS
        (service name), not localhost."""
        data = self._load()
        d_env = data["services"]["daemon"]["environment"]
        assert "http://qdrant:" in d_env["QDRANT_URL"]

    def test_rag_server_port_published(self):
        data = self._load()
        rag = data["services"]["rag_server"]
        ports = rag["ports"]
        # Port 8000 should be exposed to the host so OpenWebUI on
        # the host (outside compose) can reach it.
        assert any("8000" in str(p) for p in ports)


class TestEnvExampleCoversAllProviders:
    """Every provider with a non-empty env_var in providers.py
    should be mentioned in .env.example.compose so users don't
    guess which variable they need to export."""

    def test_all_provider_env_vars_present(self):
        from throughline_cli import providers as pr
        env_example = (REPO_ROOT / ".env.example.compose").read_text(
            encoding="utf-8")
        missing = []
        for preset in pr.list_presets():
            # Skip placeholder env vars that aren't meant to be set
            # (Ollama's doesn't require a key for vanilla installs;
            # LM Studio's is a forks-only concern; Generic reuses
            # THROUGHLINE_LLM_API_KEY).
            if preset.id in ("ollama", "lm_studio", "generic"):
                continue
            if preset.env_var not in env_example:
                missing.append(f"{preset.id} ({preset.env_var})")
        assert not missing, (
            f"Provider env vars missing from .env.example.compose: {missing}"
        )

    def test_default_embedder_reasonable_for_minimal_build(self):
        env_example = (REPO_ROOT / ".env.example.compose").read_text(
            encoding="utf-8")
        # Minimal image skips torch; default EMBEDDER should be
        # cloud-capable, not bge-m3.
        assert "EMBEDDER=openai" in env_example


class TestDockerfile:
    def test_exists(self):
        assert (REPO_ROOT / "Dockerfile").exists()

    def test_install_local_arg_declared(self):
        """The opt-in to local torch + transformers is a build ARG."""
        df = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
        assert "INSTALL_LOCAL" in df
        # Default 0 keeps the image small; users opt in explicitly.
        assert "INSTALL_LOCAL=0" in df

    def test_workdir_matches_container_paths(self):
        df = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
        # The ENV settings + volumes in compose both use /data/...
        # paths. Match them.
        assert "WORKDIR /app" in df
        assert "/data/vault" in df
        assert "/data/state" in df
