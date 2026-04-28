"""Phase 1.5 polish — `--doctor` subcommand + `wait_for_refine` impl.

Two clusters of tests:

- TestDoctorChecks: each individual check function in
  `mcp_server.doctor` is invoked against contrived environments
  (missing dirs / unreachable rag / missing taxonomy module) and
  verified to fire the right status.
- TestWaitForTerminalStatus: `daemon_writer.wait_for_terminal_status`
  is fed a fake refine_state.json and verified to:
    * return early on terminal status
    * timeout cleanly when no terminal status is written
    * tolerate mid-write JSON corruption (skip + retry)
- TestSaveConversationWaitForRefine: end-to-end test that the
  save_conversation tool, when called with wait_for_refine=True,
  surfaces the daemon's terminal status in the return shape.

All tests stub at the boundary — no real subprocess, no real
network, no real fastmcp.
"""
from __future__ import annotations

import json
import time
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import pytest


# ---------- doctor ----------

class TestDoctorChecks:
    def test_check_raw_root_present(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path))
        from mcp_server.doctor import _check_raw_root

        ok = _check_raw_root()
        assert ok is True
        assert "[ok]" in capsys.readouterr().out

    def test_check_raw_root_missing(self, tmp_path, monkeypatch, capsys):
        missing = tmp_path / "definitely_missing"
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(missing))
        from mcp_server.doctor import _check_raw_root

        ok = _check_raw_root()
        assert ok is False
        out = capsys.readouterr().out
        assert "[fail]" in out
        assert "install.py --express" in out  # remediation hint

    def test_check_vault_root_missing_is_warn_not_fail(
        self, tmp_path, monkeypatch, capsys
    ):
        """Missing vault is OK pre-daemon-start; doctor should warn,
        not fail."""
        missing = tmp_path / "no_vault_yet"
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(missing))
        from mcp_server.doctor import _check_vault_root

        result = _check_vault_root()
        assert result is True  # warnings don't return False
        assert "[warn]" in capsys.readouterr().out

    def test_check_rag_server_unreachable(self, capsys):
        from mcp_server.doctor import _check_rag_server

        with patch(
            "urllib.request.urlopen",
            side_effect=URLError("Connection refused"),
        ):
            ok = _check_rag_server()
        assert ok is False
        out = capsys.readouterr().out
        assert "[fail]" in out
        assert "rag_server.py" in out

    def test_check_rag_server_reachable(self, capsys):
        from mcp_server.doctor import _check_rag_server
        from unittest.mock import MagicMock

        fake = MagicMock()
        fake.status = 200
        fake.__enter__ = MagicMock(return_value=fake)
        fake.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=fake):
            ok = _check_rag_server()
        assert ok is True
        assert "[ok]" in capsys.readouterr().out

    def test_reflection_state_files_all_missing_warns(
        self, monkeypatch, tmp_path, capsys,
    ):
        """No state files at all → emits 'no Reflection Pass state
        files found' warn."""
        from mcp_server.doctor import _check_reflection_state_files

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "empty"))
        ok = _check_reflection_state_files()
        assert ok is False
        out = capsys.readouterr().out
        assert "[warn]" in out
        assert "no Reflection Pass state files found" in out

    def test_reflection_state_files_present_ok(
        self, monkeypatch, tmp_path, capsys,
    ):
        from mcp_server.doctor import _check_reflection_state_files

        # Write a valid positions.json so check finds at least one
        # state file
        (tmp_path / "reflection_positions.json").write_text(
            '{"clusters": []}', encoding="utf-8"
        )
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        ok = _check_reflection_state_files()
        assert ok is True
        out = capsys.readouterr().out
        assert "[ok] reflection.positions" in out

    def test_reflection_state_files_stale_warns(
        self, monkeypatch, tmp_path, capsys,
    ):
        """File present but older than the staleness threshold (14d)
        emits a warn pointing the user at re-running the pass or
        installing the auto-schedule template."""
        import os
        import time
        from mcp_server.doctor import _check_reflection_state_files

        f = tmp_path / "reflection_positions.json"
        f.write_text('{"clusters": []}', encoding="utf-8")
        # Backdate to 20 days old (well past the 14d threshold).
        old = time.time() - 20 * 86400
        os.utime(f, (old, old))

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        ok = _check_reflection_state_files()
        # Function still returns True (positions file is present); the
        # staleness is a warning, not a blocking failure.
        assert ok is True
        out = capsys.readouterr().out
        assert "[warn]" in out
        assert "stale" in out.lower()
        assert "reflection_pass" in out

    def test_check_daemon_taxonomy_importable(self, capsys):
        from mcp_server.doctor import _check_daemon_taxonomy_import

        ok = _check_daemon_taxonomy_import()
        assert ok is True
        assert "[ok]" in capsys.readouterr().out

    def test_check_daemon_taxonomy_empty_warns(
        self, monkeypatch, capsys
    ):
        import daemon.taxonomy
        monkeypatch.setattr(daemon.taxonomy, "VALID_X_SET", [])
        from mcp_server.doctor import _check_daemon_taxonomy_import

        ok = _check_daemon_taxonomy_import()
        assert ok is False  # empty IS a fail-ish, returns False
        out = capsys.readouterr().out
        assert "[warn]" in out

    def test_run_doctor_returns_zero_when_all_pass(
        self, tmp_path, monkeypatch, capsys
    ):
        """Stitch all checks together. RAG server mocked reachable;
        taxonomy import works; raw_root + vault_root present.
        fastmcp may not be installed in test env — the runner will
        report it but we accept that."""
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "raw"))
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path / "vault"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        (tmp_path / "raw").mkdir()
        (tmp_path / "vault").mkdir()

        from mcp_server.doctor import run_doctor
        from unittest.mock import MagicMock

        fake_resp = MagicMock()
        fake_resp.status = 200
        fake_resp.__enter__ = MagicMock(return_value=fake_resp)
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=fake_resp):
            # Skip the fastmcp check by mocking it as installed
            with patch("mcp_server.doctor._check_fastmcp",
                       return_value=True):
                exit_code = run_doctor()
        assert exit_code == 0

    def test_run_doctor_returns_nonzero_when_required_fails(
        self, tmp_path, monkeypatch, capsys
    ):
        """RAW_ROOT missing → fail → exit 1."""
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "no_raw"))
        # Vault present so it doesn't taint the result
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path / "vault"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        (tmp_path / "vault").mkdir()

        from mcp_server.doctor import run_doctor
        from unittest.mock import MagicMock

        fake_resp = MagicMock()
        fake_resp.status = 200
        fake_resp.__enter__ = MagicMock(return_value=fake_resp)
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=fake_resp):
            with patch("mcp_server.doctor._check_fastmcp",
                       return_value=True):
                exit_code = run_doctor()
        assert exit_code == 1


# ---------- __main__ subcommand dispatch ----------

class TestMainSubcommands:
    def test_help_flag_returns_zero(self, capsys):
        from mcp_server.__main__ import main

        rc = main(["--help"])
        assert rc == 0
        assert "throughline-mcp" in capsys.readouterr().out

    def test_short_help(self, capsys):
        from mcp_server.__main__ import main

        rc = main(["-h"])
        assert rc == 0

    def test_version_flag(self, capsys):
        from mcp_server.__main__ import main

        rc = main(["--version"])
        assert rc == 0
        out = capsys.readouterr().out.strip()
        # Should be a version-like string
        assert len(out) > 0
        assert "." in out  # at least major.minor

    def test_unknown_flag_returns_2(self, capsys):
        from mcp_server.__main__ import main

        rc = main(["--bogus"])
        assert rc == 2

    def test_doctor_flag_invokes_doctor(self, tmp_path, monkeypatch, capsys):
        """`python -m mcp_server --doctor` calls run_doctor and
        propagates its exit code."""
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "no_raw"))
        from mcp_server.__main__ import main
        from unittest.mock import MagicMock

        # mock everything to avoid real network / disk dependency
        with patch("mcp_server.doctor._check_fastmcp", return_value=True):
            with patch("mcp_server.doctor._check_rag_server",
                       return_value=True):
                with patch("mcp_server.doctor._check_daemon_taxonomy_import",
                           return_value=True):
                    rc = main(["--doctor"])
        assert rc == 1  # raw_root missing → fail


# ---------- wait_for_terminal_status ----------

class TestWaitForTerminalStatus:
    def test_returns_immediately_when_terminal_status_already_written(
        self, tmp_path
    ):
        """If the daemon already finished by the time we poll,
        return on the first iteration."""
        from mcp_server.daemon_writer import wait_for_terminal_status

        state_dir = tmp_path
        raw_path = tmp_path / "fake.md"
        key = str(raw_path).replace("\\", "/")

        state = {"files": {key: {"raw_hash": "x", "status": "ok",
                                  "cards": 1}}}
        (state_dir / "refine_state.json").write_text(
            json.dumps(state), encoding="utf-8")

        status, entry = wait_for_terminal_status(
            raw_path=raw_path, state_dir=state_dir,
            timeout_s=2.0, poll_interval_s=0.01,
        )
        assert status == "ok"
        assert entry is not None
        assert entry["cards"] == 1

    def test_returns_each_terminal_status(self, tmp_path):
        """Verify all 8 documented terminal statuses get returned
        as-is (not coerced or filtered)."""
        from mcp_server.daemon_writer import (
            _TERMINAL_STATUSES,
            wait_for_terminal_status,
        )

        for status_value in _TERMINAL_STATUSES:
            raw_path = tmp_path / f"fake_{status_value}.md"
            key = str(raw_path).replace("\\", "/")
            state = {"files": {key: {"raw_hash": "x",
                                      "status": status_value}}}
            (tmp_path / "refine_state.json").write_text(
                json.dumps(state), encoding="utf-8")

            result_status, _ = wait_for_terminal_status(
                raw_path=raw_path, state_dir=tmp_path,
                timeout_s=1.0, poll_interval_s=0.01,
            )
            assert result_status == status_value, (
                f"Expected {status_value}, got {result_status}"
            )

    def test_times_out_when_status_never_written(self, tmp_path):
        """No state file → poll until deadline → return 'timeout'."""
        from mcp_server.daemon_writer import wait_for_terminal_status

        raw_path = tmp_path / "fake.md"
        start = time.time()
        status, entry = wait_for_terminal_status(
            raw_path=raw_path, state_dir=tmp_path,
            timeout_s=0.3, poll_interval_s=0.05,
        )
        elapsed = time.time() - start
        assert status == "timeout"
        assert entry is None
        assert 0.25 <= elapsed <= 1.0  # roughly the timeout

    def test_times_out_when_only_non_terminal_status(self, tmp_path):
        """Even if the file is in state, a non-terminal status
        keeps polling (e.g. mid-process the daemon could write
        intermediate states; we don't see those today but be
        defensive)."""
        from mcp_server.daemon_writer import wait_for_terminal_status

        raw_path = tmp_path / "fake.md"
        key = str(raw_path).replace("\\", "/")
        state = {"files": {key: {"raw_hash": "x",
                                  "status": "in_progress"}}}
        (tmp_path / "refine_state.json").write_text(
            json.dumps(state), encoding="utf-8")

        status, _ = wait_for_terminal_status(
            raw_path=raw_path, state_dir=tmp_path,
            timeout_s=0.2, poll_interval_s=0.05,
        )
        assert status == "timeout"

    def test_tolerates_mid_write_corruption(self, tmp_path):
        """If we read refine_state.json while daemon is mid-write
        (theoretical race window), JSON parse fails — we should
        sleep + retry, not crash."""
        from mcp_server.daemon_writer import wait_for_terminal_status

        raw_path = tmp_path / "fake.md"
        key = str(raw_path).replace("\\", "/")

        # Write garbage first, then valid terminal state
        (tmp_path / "refine_state.json").write_text(
            "{ not valid json {", encoding="utf-8")

        # Schedule a fix after a short delay
        import threading
        def _fix():
            time.sleep(0.1)
            (tmp_path / "refine_state.json").write_text(
                json.dumps({"files": {key: {"raw_hash": "x",
                                             "status": "ok"}}}),
                encoding="utf-8",
            )
        threading.Thread(target=_fix, daemon=True).start()

        status, entry = wait_for_terminal_status(
            raw_path=raw_path, state_dir=tmp_path,
            timeout_s=2.0, poll_interval_s=0.05,
        )
        assert status == "ok"


# ---------- save_conversation wait_for_refine integration ----------

class TestSaveConversationWaitForRefine:
    def test_default_does_not_wait(self, tmp_path, monkeypatch):
        """wait_for_refine=False (default) returns immediately,
        no daemon_status field."""
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "raw"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        (tmp_path / "raw").mkdir()
        from mcp_server.tools import save_conversation

        result = save_conversation(text="## user\nhi")
        assert result["_status"] == "ok"
        assert "daemon_status" not in result

    def test_wait_for_refine_returns_daemon_status(
        self, tmp_path, monkeypatch
    ):
        """wait_for_refine=True polls + surfaces the daemon's
        terminal status."""
        raw_root = tmp_path / "raw"
        state_dir = tmp_path / "state"
        raw_root.mkdir()
        state_dir.mkdir()
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(raw_root))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state_dir))

        from mcp_server.tools import save_conversation

        # Pre-write a terminal state for ANY future raw file. The
        # save_conversation call writes to a unique conv_id'd path,
        # so we need to monkeypatch the wait helper to short-circuit
        # OR use a different approach. Cleanest: patch
        # wait_for_terminal_status to return immediately.
        with patch(
            "mcp_server.tools.save_conversation.wait_for_terminal_status",
            return_value=("ok", {"raw_hash": "x", "status": "ok",
                                  "cards": 1}),
        ):
            result = save_conversation(text="## user\nhi",
                                        wait_for_refine=True)

        assert result["_status"] == "ok"
        assert result.get("daemon_status") == "ok"

    def test_wait_for_refine_surfaces_timeout(
        self, tmp_path, monkeypatch
    ):
        """If the daemon doesn't process in time, daemon_status
        is 'timeout' (not an error — the file was queued OK)."""
        raw_root = tmp_path / "raw"
        state_dir = tmp_path / "state"
        raw_root.mkdir()
        state_dir.mkdir()
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(raw_root))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state_dir))

        from mcp_server.tools import save_conversation

        with patch(
            "mcp_server.tools.save_conversation.wait_for_terminal_status",
            return_value=("timeout", None),
        ):
            result = save_conversation(text="## user\nhi",
                                        wait_for_refine=True)

        # File was queued successfully — _status='ok'
        assert result["_status"] == "ok"
        # But the daemon didn't finish in time — surfaced separately
        assert result.get("daemon_status") == "timeout"
