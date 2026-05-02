# `#b-encryption` — At-rest SQLite encryption + per-user key derivation

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: wave3-plan-architect. 2026-05-03.

## 1. Goal

Wave 3 (post-Phase-1-alpha): add at-rest encryption for the SQLite vault and derive per-user encryption keys from auth credentials. **Phase 1 alpha ships at-rest plaintext.** This is honest disclosure per friends-intro: *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture). Encryption hardening on the post-launch roadmap. Export is plaintext markdown — that's the actual ownership story."* The goal of `#b-encryption` is to *harden* against passive disk compromise, not to claim zero-knowledge.

## 2. Strategic context

Brand-book §7 Decision 6 commits to honesty about architectural compromises; `#b-encryption` operationalizes that commitment without overpromising. Server-side recall *requires* plaintext access to user cards during query — therefore zero-knowledge is structurally unavailable. Adding at-rest encryption protects the vault file at disk-rest (laptop theft, cloud snapshot leak, compromised backup) without claiming a property the architecture cannot deliver.

## 3. Design options

(a) **SQLCipher** — battle-tested AES-256 page-level encryption for SQLite, Python bindings via `pysqlcipher3`, transparent to the application layer. ~5% perf overhead measured by upstream. Mature (originated 2008, used by 1Password / Signal historically). Free for community use; commercial license available.

(b) **SQLite Encryption Extension (SEE)** — Hwaci's official commercial extension, $2k-3k one-time license. Closed-source. Same API surface as SQLCipher. Reject: cost-vs-value is poor at Phase 1; SQLCipher provides equivalent protection with no upfront license.

(c) **Application-level field encryption** — encrypt only sensitive columns (card body, conversation transcripts) in app code with per-user keys; metadata stays plaintext. Pros: granular; metadata indexes still queryable without decryption. Cons: FTS5 trigram index on encrypted columns becomes useless (cards search breaks); vec0 cosine search on encrypted embeddings becomes useless (active recall breaks).

## 4. Recommended approach

**SQLCipher with per-user key derived from Clerk auth_user_id + server-held master salt** via Argon2id KDF (params: t=2, m=64 MiB, p=1; ~50ms per derivation on commodity hardware). Server holds the master salt; per-user salt derived from auth_user_id; key never persisted at rest in plaintext. Backups encrypted at the page level (the SQLite file is end-to-end ciphertext).

This is **NOT zero-knowledge.** During recall the server decrypts the user's vault into RAM, runs FTS5 + vec0 queries, returns matched cards, then drops the decrypted handle. Anthropic API calls remain unencrypted in transit (TLS 1.3 only). Marketing copy must align with brand-book §7 Decision 6 anti-spin discipline: market this as "encryption at rest, recall server-trusted" — never as "end-to-end encrypted."

## 5. Vendor / tool choice

**SQLCipher community edition** (BSD-style license, free). Python binding `pysqlcipher3==1.x`. KDF: `argon2-cffi` (Python). No vendor lock-in — SQLCipher is open-source; rotating away from it means migrating files via `ATTACH ... KEY ''` SQL pattern (well-documented).

## 6. Legal / compliance audit

GDPR Article 32 ("appropriate technical measures"): at-rest encryption supports a stronger data-protection claim in privacy policy. Sensitive personal data per Article 9 (mental-health / political / sexual-orientation conversational disclosures) — encryption-at-rest is the minimum baseline, not sufficient on its own (still requires geo-block + DPO + breach notification within 72hr). Disclosure: privacy policy (`#b-privacy-policy`) must state explicitly that encryption is at-rest only, recall is server-trusted, and Anthropic API processes plaintext content in transit. **Do not let marketing copy say "encrypted" without qualifier — that is the lie the friends-intro prohibits.**

## 7. Rollback / migration if vendor changes

SQLCipher → unencrypted SQLite migration: `ATTACH 'plain.db' AS plain KEY ''; SELECT sqlcipher_export('plain'); DETACH plain;` (one-line operation per user vault). Migration time: ~30s per 100MB vault. Lock-in: low.

## 8. Cost estimate

Phase 1 (NOT shipped): $0. Wave 3 deployed: SQLCipher binary +5MB per platform; runtime overhead ~5% on read, ~3% on write (per upstream benchmarks). Argon2id key derivation ~50ms once per session. Compute cost increase at $10k MRR scale: ~$5-10/mo additional CPU on Railway/Hetzner. Engineering cost: 5-7 days implementation + 2 days migration testing of existing alpha vaults.

## 9. Lead-time blockers

External: zero (SQLCipher is FOSS). Internal: 5-7 days implementation; cannot ship until `#b-auth` ships (per-user key requires authenticated user); cannot run on existing alpha vaults without migration tooling that quiesces the vault during re-encryption. Estimated end-to-end: **2 weeks calendar after `#b-auth` lands.**

## 10. Open decisions for Rodc (Type-A)

- **TA-1:** Wave 3 timing — does encryption ship before paid pricing (signal-to-paying-users), or after (don't gate alpha on it)? Recommendation: after, per friends-intro honest disclosure stance.
- **TA-2:** User-controlled encryption mode (allow user to set their own passphrase, server stores nothing) vs server-controlled mode (current proposal, server holds salt). User-controlled is closer to zero-knowledge but loses recall. Recommendation: server-controlled at Wave 3, evaluate user-controlled mode at Wave 4 if alpha telemetry shows demand.
- **TA-3:** Marketing register lock — confirm "encryption at rest, recall server-trusted" exact phrasing, never "end-to-end encrypted."

## 11. Implementation outline (high-level)

1. Add `encryption_status` column to user record; `'plaintext'` for grandfathered alpha vaults, `'sqlcipher_v1'` for new.
2. Implement `encrypt_existing_vault(auth_user_id)` migration: derive key, ATTACH ciphertext DB, copy rows, DETACH, swap files, atomically.
3. Wire SQLCipher PRAGMA key into `sqlite_adapter.py` connection-open path.
4. Add boot-time decryption check + key-derivation cache (per-process LRU, max 100 entries, 1hr TTL).
5. Document the architecture honestly in `app/web/docs/privacy.md`.

## 12. Risk register

1. **Marketing drift toward "encrypted"-without-qualifier** — high probability over 24mo; mitigated by brand-book §7 Decision 6 lock + style-guide enforcement at all copy review.
2. **Argon2id parameters too aggressive on cheap mobile-first deploys** — re-tune per device class.
3. **Backup pipeline forgets to encrypt** — backup tooling (`#b-deploy`) must read SQLCipher file as ciphertext blob; verify with explicit test.
