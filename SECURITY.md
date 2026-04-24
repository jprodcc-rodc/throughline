# Security policy

For the full threat-model breakdown (what the system defends
against, what it doesn't, and hardening recommendations), see
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md). This file is the
shorter "how to report" reference.

## Reporting a vulnerability

**Don't open a public issue.** For anything that could affect users'
data safety — credential leakage, path traversal, prompt injection
that escalates beyond a single card, SSRF against Qdrant / the RAG
server, etc. — please report privately.

Preferred channel: **GitHub's private security advisory** at
<https://github.com/jprodcc-rodc/throughline/security/advisories/new>.
That opens a confidential thread only the maintainer can see.

Include:
- a minimal reproduction (fixture / command / network trace);
- the impact you've confirmed (data disclosure, RCE, DoS, …);
- whether the issue is already public anywhere.

## Scope

In scope:
- `daemon/` — the refine pipeline and its state files
- `rag_server/` — the FastAPI endpoints (`/v1/embeddings`,
  `/v1/rerank`, `/v1/rag`, `/refine_status`)
- `throughline_cli/` — install wizard + import adapters
- `packs/` — pack runtime loading arbitrary YAML + prompts
- anything that writes under `~/.throughline/` or the user's vault

Out of scope (report upstream instead):
- vulnerabilities in Qdrant, OpenWebUI, PyTorch, Transformers,
  FastAPI, or any other pinned dependency — those live with their
  respective projects.
- misuse of a user's own API keys that the user placed in their
  shell environment.

## Response

This is a solo-maintained alpha project. A first acknowledgement
should land within 5 working days. Fix timelines depend on severity
and my day job — critical issues (active exploitation, credential
exposure) get prioritised over cosmetic ones.

## Disclosure

Unless you ask otherwise, a published fix will credit the reporter
in the release notes.
