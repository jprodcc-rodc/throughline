"""Tests for daemon.open_threads.

Coverage:
- Tokenizer handles English, Chinese, mixed, with stopword filtering
- _question_addressed_by threshold semantics (HIGH conservative bias)
- _card_timestamp falls back gracefully through frontmatter.date /
  .updated / file mtime / "0" sentinel
- detect_open_threads: empty grouped, single-card cluster (always
  open), back-filled chronological cluster (later card addresses
  earlier question), edge cases (no questions, dates missing)
"""
from __future__ import annotations

from pathlib import Path

import pytest


# ---------- _tokenize ----------

class TestTokenize:
    def test_english_words(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("How does freemium conversion work?")
        # 'how' / 'does' are stopwords; rest stays
        assert "freemium" in out
        assert "conversion" in out
        assert "work" in out
        assert "how" not in out
        assert "does" not in out

    def test_chinese_bigrams(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("如何处理用药剂量")
        # Bigrams of consecutive CJK chars
        assert "处理" in out
        assert "用药" in out
        assert "剂量" in out
        # Stopword bigram ("如何") filtered
        assert "如何" not in out

    def test_mixed_language(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("freemium 转化策略 vs 订阅 model")
        assert "freemium" in out
        assert "model" in out
        # Chinese bigrams from runs
        assert "转化" in out
        assert "策略" in out
        assert "订阅" in out

    def test_punctuation_split(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("term1, term2; term3 — term4!")
        assert {"term1", "term2", "term3", "term4"}.issubset(out)

    def test_short_tokens_dropped(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("a x of stuff")
        assert "a" not in out
        assert "x" not in out
        assert "stuff" in out  # 5 chars, kept

    def test_lowercased(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("Freemium AND Pricing")
        assert "freemium" in out
        assert "pricing" in out
        assert "and" not in out  # stopword
        # Original case absent
        assert "Freemium" not in out

    def test_empty_input(self):
        from daemon.open_threads import _tokenize

        assert _tokenize("") == set()
        assert _tokenize("   ") == set()


# ---------- _question_addressed_by ----------

class TestQuestionAddressed:
    def test_full_overlap_addresses(self):
        from daemon.open_threads import _question_addressed_by

        q = "how to handle freemium conversion?"
        text = "freemium conversion strategy detailed playbook"
        # q tokens: {freemium, conversion, handle}
        # text tokens: {freemium, conversion, strategy, detailed, playbook}
        # overlap 2/3 = 0.67 -> below 0.75 -> NOT addressed
        assert _question_addressed_by(q, text, threshold=0.75) is False
        # At lower threshold it does address
        assert _question_addressed_by(q, text, threshold=0.5) is True

    def test_no_overlap_not_addressed(self):
        from daemon.open_threads import _question_addressed_by

        q = "freemium conversion handling"
        text = "PostgreSQL vacuum tuning playbook"
        assert _question_addressed_by(q, text) is False

    def test_chinese_question_addressed(self):
        from daemon.open_threads import _question_addressed_by

        q = "B1 注射剂量如何调整"
        # candidate has B1, 注射, 剂量, 调整 covered
        text = "B1 注射剂量阶梯调整方案"
        # Force a candidate big enough to hit threshold
        assert _question_addressed_by(q, text, threshold=0.5) is True

    def test_empty_question_not_addressed(self):
        """Edge: empty / all-stopword question. Don't claim it's
        addressed — that would let stage 5 silently swallow weird
        upstream output."""
        from daemon.open_threads import _question_addressed_by

        assert _question_addressed_by("", "anything") is False
        assert _question_addressed_by("the and or", "the and or") is False

    def test_empty_candidate_not_addressed(self):
        from daemon.open_threads import _question_addressed_by

        assert _question_addressed_by("freemium conversion", "") is False


# ---------- _card_timestamp ----------

class TestCardTimestamp:
    def test_date_field_used(self):
        from daemon.open_threads import _card_timestamp

        c = {"frontmatter": {"date": "2026-01-15"}, "path": "/x"}
        assert _card_timestamp(c) == "2026-01-15"

    def test_updated_when_no_date(self):
        from daemon.open_threads import _card_timestamp

        c = {"frontmatter": {"updated": "2026-02-20"}, "path": "/x"}
        assert _card_timestamp(c) == "2026-02-20"

    def test_date_takes_precedence_over_updated(self):
        from daemon.open_threads import _card_timestamp

        c = {
            "frontmatter": {"date": "2026-01-15", "updated": "2026-03-01"},
            "path": "/x",
        }
        assert _card_timestamp(c) == "2026-01-15"

    def test_falls_back_to_mtime(self, tmp_path):
        from daemon.open_threads import _card_timestamp

        p = tmp_path / "card.md"
        p.write_text("body", encoding="utf-8")
        c = {"frontmatter": {}, "path": str(p)}
        ts = _card_timestamp(c)
        assert ts.startswith("mtime-")

    def test_zero_when_nothing_resolvable(self):
        from daemon.open_threads import _card_timestamp

        c = {"frontmatter": {}, "path": "/nonexistent"}
        assert _card_timestamp(c) == "0"

    def test_handles_non_dict_frontmatter(self):
        from daemon.open_threads import _card_timestamp

        c = {"frontmatter": "garbled yaml", "path": "/nonexistent"}
        assert _card_timestamp(c) == "0"


# ---------- detect_open_threads ----------

class TestDetectOpenThreads:
    def test_empty_grouped_returns_empty(self):
        from daemon.open_threads import detect_open_threads

        assert detect_open_threads({}) == {}

    def test_no_questions_returns_empty(self):
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {"path": "a.md", "title": "A", "body": "body",
                 "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {"claim_summary": "X", "open_questions": []}},
                {"path": "b.md", "title": "B", "body": "body",
                 "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {"claim_summary": "Y", "open_questions": []}},
            ]
        }
        assert detect_open_threads(grouped) == {}

    def test_single_card_with_questions_always_open(self):
        """No later card to potentially address → all questions
        marked still-open."""
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {"path": "a.md", "title": "A", "body": "body",
                 "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {
                     "claim_summary": "X",
                     "open_questions": ["how to handle freemium conversion?"],
                 }},
            ]
        }
        out = detect_open_threads(grouped)
        assert out == {"a.md": ["how to handle freemium conversion?"]}

    def test_later_card_addresses_question(self):
        """Earlier card raises a question; a later card mentions
        the question's vocabulary heavily → marked addressed →
        not in result."""
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {"path": "early.md", "title": "Early discussion",
                 "body": "Open question section",
                 "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {
                     "claim_summary": "Discussing freemium conversion handling",
                     "open_questions": ["freemium conversion handling strategy"],
                 }},
                {"path": "late.md",
                 "title": "Freemium conversion handling strategy resolved",
                 "body": "freemium conversion handling strategy decision",
                 "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {
                     "claim_summary": "Concluded the freemium conversion approach",
                     "open_questions": [],
                 }},
            ]
        }
        out = detect_open_threads(grouped, threshold=0.75)
        # "early.md" should have its question addressed by "late.md"
        # whose title literally repeats the question phrase.
        assert "early.md" not in out

    def test_later_card_doesnt_address_unrelated(self):
        """Even with a later card present, an unrelated question
        stays open."""
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {"path": "a.md", "title": "Topic A",
                 "body": "stuff about widgets",
                 "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {
                     "claim_summary": "Widgets",
                     "open_questions": ["how to optimize SQL query plans?"],
                 }},
                {"path": "b.md", "title": "Topic A continued",
                 "body": "more widgets discussion",
                 "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {
                     "claim_summary": "Widgets continued",
                     "open_questions": [],
                 }},
            ]
        }
        out = detect_open_threads(grouped)
        assert out == {"a.md": ["how to optimize SQL query plans?"]}

    def test_chronological_ordering_by_date(self):
        """Order matters — questions only checked against LATER
        cards, not earlier ones."""
        from daemon.open_threads import detect_open_threads

        # Sequence chronologically: card_b (2026-01) then card_a
        # (2026-02). Card_a has the question; card_b precedes it
        # so cannot 'address' it.
        grouped = {
            "0": [
                {"path": "card_a.md",
                 "title": "Later card with the question",
                 "body": "freemium conversion strategy",
                 "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {
                     "claim_summary": "Freemium conversion strategy",
                     "open_questions": ["freemium conversion strategy"],
                 }},
                {"path": "card_b.md",
                 "title": "freemium conversion strategy",
                 "body": "freemium conversion strategy",
                 "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {
                     "claim_summary": "freemium conversion strategy",
                     "open_questions": [],
                 }},
            ]
        }
        out = detect_open_threads(grouped, threshold=0.75)
        # card_a's question is the LAST chronologically → no later
        # card → marked open. card_b is before, can't address.
        assert "card_a.md" in out

    def test_chinese_question_resolution(self):
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {"path": "early.md", "title": "B1 治疗方案",
                 "body": "讨论 B1 注射剂量",
                 "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {
                     "claim_summary": "B1 注射方案",
                     "open_questions": ["B1 注射剂量阶梯调整"],
                 }},
                {"path": "late.md",
                 "title": "B1 注射剂量阶梯调整方案",
                 "body": "B1 注射剂量阶梯调整决策",
                 "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {
                     "claim_summary": "B1 注射剂量阶梯调整",
                     "open_questions": [],
                 }},
            ]
        }
        out = detect_open_threads(grouped, threshold=0.5)
        assert "early.md" not in out

    def test_partial_resolution(self):
        """Card has 3 questions; later cards address 1; remaining
        2 stay open."""
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {"path": "a.md", "title": "Topic",
                 "body": "discussing freemium",
                 "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {
                     "claim_summary": "Topic",
                     "open_questions": [
                         "freemium conversion handling strategy",
                         "database scaling beyond 10K writes per second",
                         "session token rotation under load",
                     ],
                 }},
                {"path": "b.md",
                 "title": "freemium conversion handling strategy",
                 "body": "freemium conversion handling strategy resolved",
                 "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {"claim_summary": "X", "open_questions": []}},
            ]
        }
        out = detect_open_threads(grouped, threshold=0.75)
        # Question 1 addressed; questions 2 and 3 stay open.
        assert "a.md" in out
        remaining = out["a.md"]
        assert len(remaining) == 2
        assert any("database" in q.lower() for q in remaining)
        assert any("session token" in q.lower() for q in remaining)

    def test_no_backfill_no_questions(self):
        """Card without _backfill shouldn't appear in results."""
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {"path": "a.md", "title": "A", "body": "x",
                 "frontmatter": {"date": "2026-01-01"}},
            ]
        }
        assert detect_open_threads(grouped) == {}
