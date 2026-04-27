"""End-to-end regression test: adapter render → daemon parser.

Catches the H1/H2 mismatch bug discovered 2026-04-27 during MCP
Phase 1 audit:
- `throughline_cli/adapters/common.py:render_markdown` had been
  emitting `# User` / `# Assistant` (H1, capitalised)
- `daemon/refine_daemon.py:_MSG_SPLIT_RE` parses
  `^## (user|assistant)\\s*$` (H2 only, case-insensitive)
- Result: every adapter-imported conversation refined to empty,
  silently. No test exercised the round-trip until now.

These tests run the actual `render_markdown()` function on a
synthetic conversation, then feed the rendered string into the
daemon's actual `_parse_messages()` function, and assert messages
come back populated. If `render_markdown` ever drifts to a format
the daemon can't parse again, this test fires immediately.
"""
from __future__ import annotations

import pytest


# ---------- The contract test (catches the exact prior bug) ----------

class TestAdapterToDaemonContract:
    """Verifies the format contract between the adapter render
    layer and the daemon parse layer holds end-to-end."""

    def test_render_markdown_produces_h2_role_markers(self):
        """Locked format contract: role markers are `## user` and
        `## assistant` (H2 lowercase). The daemon parser treats
        anything else as content, not a turn boundary."""
        from throughline_cli.adapters.common import render_markdown

        body = render_markdown(
            title="Test conversation",
            messages=[
                ("user", "first question"),
                ("assistant", "first answer"),
            ],
            metadata={"title": "Test conversation",
                      "date": "2026-04-27",
                      "source_platform": "test"},
        )

        assert "## user" in body
        assert "## assistant" in body
        # The OLD broken format must NOT reappear
        assert "# User\n" not in body
        assert "# Assistant\n" not in body

    def test_round_trip_through_daemon_parser(self):
        """The full contract test: adapter renders → daemon's
        _parse_messages reads back the original turn structure."""
        from throughline_cli.adapters.common import render_markdown
        from daemon.refine_daemon import _parse_messages

        rendered = render_markdown(
            title="Pricing decision",
            messages=[
                ("user", "What pricing model should I use?"),
                ("assistant", "Three considerations: LTV, churn, runway."),
                ("user", "Which matters most pre-PMF?"),
                ("assistant", "Runway. You can't iterate from a corpse."),
            ],
            metadata={
                "title": "Pricing decision",
                "date": "2026-04-27",
                "source_platform": "claude_export",
                "source_conversation_id": "abc123",
            },
        )

        # The daemon's parser ignores frontmatter; we feed it the
        # body region after `---\n.*\n---\n`.
        body_after_fm = rendered.split("---\n", 2)[-1]
        messages = _parse_messages(body_after_fm)

        # Pre-bug behaviour was zero messages parsed.
        # Post-fix: 4 messages parsed in correct order with content.
        assert len(messages) == 4

        assert messages[0].role == "user"
        assert "pricing model" in messages[0].content

        assert messages[1].role == "assistant"
        assert "LTV" in messages[1].content

        assert messages[2].role == "user"
        assert "pre-PMF" in messages[2].content

        assert messages[3].role == "assistant"
        assert "Runway" in messages[3].content

    def test_round_trip_handles_multi_paragraph_content(self):
        """Daemon must keep paragraph breaks inside a single turn."""
        from throughline_cli.adapters.common import render_markdown
        from daemon.refine_daemon import _parse_messages

        long_content = (
            "Short opener.\n\n"
            "Second paragraph with more detail.\n\n"
            "Third paragraph wraps it up."
        )
        rendered = render_markdown(
            title="t",
            messages=[("user", long_content)],
            metadata={"title": "t"},
        )

        body = rendered.split("---\n", 2)[-1]
        messages = _parse_messages(body)

        assert len(messages) == 1
        assert "Short opener" in messages[0].content
        assert "Second paragraph" in messages[0].content
        assert "Third paragraph" in messages[0].content

    def test_round_trip_with_no_title_still_parses(self):
        """Title is optional; messages still get parsed without it."""
        from throughline_cli.adapters.common import render_markdown
        from daemon.refine_daemon import _parse_messages

        rendered = render_markdown(
            title="",
            messages=[
                ("user", "q"),
                ("assistant", "a"),
            ],
            metadata={"date": "2026-04-27"},
        )
        body = rendered.split("---\n", 2)[-1]
        messages = _parse_messages(body)
        assert len(messages) == 2

    def test_round_trip_preserves_role_order(self):
        """Order matters — slicer indices are 1-based on original
        turn sequence."""
        from throughline_cli.adapters.common import render_markdown
        from daemon.refine_daemon import _parse_messages

        rendered = render_markdown(
            title="t",
            messages=[
                ("assistant", "AI starts (unusual but valid)"),
                ("user", "user replies"),
                ("assistant", "AI responds"),
            ],
            metadata={"title": "t"},
        )
        body = rendered.split("---\n", 2)[-1]
        messages = _parse_messages(body)

        assert [m.role for m in messages] == ["assistant", "user", "assistant"]


# ---------- format-only sanity checks ----------

def test_render_markdown_role_lowercased_in_marker():
    """Even if input role is mixed-case ('User'), output must
    lowercase to match daemon parser regex group."""
    from throughline_cli.adapters.common import render_markdown

    body = render_markdown(
        title="t",
        messages=[("USER", "x"), ("Assistant", "y")],
        metadata={},
    )
    # Should normalise to lowercase
    assert "## user" in body
    assert "## assistant" in body
    assert "## USER" not in body
    assert "## Assistant" not in body


def test_render_markdown_empty_messages_produces_valid_doc():
    """Edge case: title-only doc with no messages still emits
    valid frontmatter and parses to zero-message body."""
    from throughline_cli.adapters.common import render_markdown
    from daemon.refine_daemon import _parse_messages

    body = render_markdown(
        title="orphan",
        messages=[],
        metadata={"title": "orphan", "date": "2026-04-27"},
    )
    body_after_fm = body.split("---\n", 2)[-1]
    messages = _parse_messages(body_after_fm)
    assert messages == []
