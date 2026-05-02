# `#b-multitenant` — Row-level isolation initially, per-user DB file at scale

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: wave3-plan-architect. 2026-05-03.

## 1. Goal

Phase 1 SaaS launch (Wave 3): convert Wave 1b's single-tenant local-first SQLite (no `user_id` column anywhere — verified across `app/shared/schema/*.sql`) into a row-isolated multi-tenant shared database. Wave 3+ at scale (>5k users, projected 18-30 months out): split into per-user SQLite file as second-stage isolation.

## 2. Strategic context

Brand-book §7 Decision 1 commits to "no shadow profile, no inferred persona label the user cannot see" — multi-tenancy must enforce the user's audit promise at the storage layer, not just at the API surface. Row-level isolation is the minimum acceptable Wave 3 ship; per-user-file is the long-term posture aligned with friends-intro "your data, your file" register.

## 3. Design options

(a) **Row-level via `user_id` column on every user-scoped table** — single shared DB, every query joins/filters on `user_id`. Smallest change to Wave 1b code (~300 LOC across 8 schemas + adapter modules). Backups simple. Cross-tenant data leak risk: medium — a missing `WHERE user_id = ?` clause anywhere ships a P0 leak. Mitigated by sqlglot-based static analysis + integration tests with seeded multi-user fixture.

(b) **Per-user SQLite file** — `<vault_root>/users/<auth_user_id>/index.db`. Maximum isolation; backup granular per user (matches "your data, your file" honesty); migration restore granular. Costs: 5x storage overhead at scale (each file carries its own FTS5 + vec0 indices); connection-pool complexity; cross-user analytics impossible without aggregation pipeline. Engineering cost: 7-10 days plus migration tooling.

(c) **Postgres with RLS (Row-Level Security)** — vendor migration away from SQLite; RLS enforced at DB level via session variable. Reject: dissolves Wave 1b's local-first FTS5 + vec0 architecture; Postgres RLS requires PG-specific extensions for vector search (pgvector). 4-6 week migration vs 2-3 days for option (a).

## 4. Recommended approach

**Option (a) at Wave 3 ship.** Path to (b) at scale. Rationale: row-level matches Wave 1b code surface (SQLite + sqlite-vec + FTS5 retained); cross-tenant leak risk is mitigated by automated static analysis; migration to per-user-file is a future-friendly path because the row-level schema *includes* user_id as a natural sharding key.

Concretely: add `user_id TEXT NOT NULL` to `cards`, `claims`, `chat_claims`, `conversations`, `messages`, `decisions`, `open_questions`, `recall_events`, `aliases`, `embedding_cache` (cache stays shared since hash-keyed). FTS5 + vec0 virtual tables get a `user_id` column too. Every adapter query gains `WHERE user_id = ?`. Integration test suite (`test_multitenant_isolation.py`) seeds 3 users + verifies no query returns cross-user rows under any access path.

## 5. Vendor / tool choice

No new vendor. SQLite + sqlite-vec + FTS5 trigram tokenizer all retained. Optional: `sqlglot` (Python lib, MIT) for static analysis to detect missing `user_id` filters at CI time.

## 6. Legal / compliance audit

GDPR Article 32 (technical measures): row-level isolation supports right-to-erasure (delete user → cascade `WHERE user_id = ?` across all tables). Article 20 (data portability): per-user markdown export already exists (`app/shared/export/markdown_exporter.py`); needs `user_id` parameterization. Sensitive personal data: cross-tenant leak in shared DB is a notifiable breach under GDPR within 72hr; row-level mitigation must be tested adversarially before Phase 1 paid launch.

## 7. Rollback / migration if vendor changes

Row-level → per-user-file migration: write `migrate_to_per_user_files.py` that reads shared DB, writes one DB per user_id, swaps mount point. Estimated: 1-2 hr per 1k users at scale. Lock-in: low because user_id is the sharding key from day one.

## 8. Cost estimate

Phase 1 (≤1,000 users, row-level): **storage ~100MB-2GB depending on conversation volume**, infrastructure overhead negligible. At $10k MRR (~5k users): ~10-50GB shared DB; FTS5 index growth dominates. Per-user-file at 50k users: ~200GB (filesystem-level overhead from index duplication). Engineering: 2-3 days for row-level, +5-7 days for per-user-file when triggered.

## 9. Lead-time blockers

External: zero (no vendor approval). Internal: blocks on `#b-auth` (need authenticated user_id source); blocks on `#b-encryption` decision (per-user key derivation must align with same user_id). Cannot ship multi-user product until both authentication + tenancy land. Estimated end-to-end: **2-3 days after `#b-auth`.**

## 10. Open decisions for Rodc (Type-A)

- **TA-1:** Trigger threshold for row-level → per-user-file migration. Recommendation: 5k active users OR 10GB shared DB OR first cross-tenant leak incident — whichever fires first.
- **TA-2:** Soft-delete vs hard-delete for right-to-erasure. Recommendation: hard-delete with 7-day grace period (audit trail in separate ops table); honors brand promise of "your data, your file."
- **TA-3:** Cross-user analytics ethics — at scale, aggregate query patterns (most-extracted topic, recall fire rate) are useful for product calibration. Brand-book §7 Decision 1 against shadow profiles. Recommendation: telemetry must be aggregated-only, never user-scoped (no individual-user behavioral analysis ever).

## 11. Implementation outline (high-level)

1. Schema migration: add `user_id` to 10 user-scoped tables + FTS5 + vec0 virtual tables.
2. Adapter migration: every SELECT/UPDATE/DELETE gains `WHERE user_id = ?`.
3. CI integration test: seed 3 users, run every query path, assert zero cross-user rows.
4. Backfill grandfathered alpha vault: assign single existing user_id to all rows.
5. sqlglot static analysis CI gate: reject PRs that add user-scoped queries without `user_id` filter.

## 12. Risk register

1. **Cross-tenant leak via missing `WHERE user_id = ?`** — high probability of a near-miss, low probability of production leak if static analysis CI gate ships. Severity: P0 GDPR breach.
2. **FTS5 trigram + per-user query performance** — at 50k users sharing FTS5 index, query latency may rise. Mitigated by per-user-file path option (b).
3. **`embedding_cache` cross-tenant pollution** — by design, embedding_cache is keyed by content hash and stays shared. Risk: a malicious user could probe whether a body was previously embedded by another user (timing attack). Acceptable at Phase 1; revisit at Wave 4.
