# throughline

> The thread that turns every LLM conversation into searchable, self-growing personal knowledge.

<!-- badges-placeholder: build / license / python-version -->

**Status:** 🚧 Alpha — the reference implementation runs 24/7 for the author, but docs and examples for external users are being cleaned up. Expect rough edges until v0.1.0 tag.

---

## ✨ What it does

```
You chat in OpenWebUI
    → conversations auto-export to Markdown
    → LLM slices / refines / de-identifies each turn
    → structured knowledge cards land in your Obsidian vault
    → local embedding + reranking builds a RAG over those cards
    → next time you ask, past knowledge is auto-injected
    → new conversation produces new cards → loop
```

Three distinctive pieces you won't find glued together elsewhere:

1. **Haiku RecallJudge** — a single small-LLM call replaces mode/aggregate/topic-shift/query-rewrite detection. Badge shows the judge's verdict inline.
2. **Concept anchors** — self-growing whitelist of entities in your vault that short-query RAG gating uses to avoid embedding drift.
3. **Personal Context cards** — 4-layer stack (Filter valve → reranker boost → `<topic>__profile.md` auto-build → optional FastAPI agent) that injects your real profile into answers without contaminating the public RAG index.

---

## 🚀 30-second demo

<!-- placeholder: animated gif of OpenWebUI badge + auto-refined card -->

---

## 📦 Quickstart

<!-- filled in Phase 5 once code migration is stable -->

```bash
# Placeholder — see docs/DEPLOYMENT.md for the canonical path.
git clone https://github.com/jprodcc-rodc/throughline
cd throughline
# TBD: install / configure / run
```

---

## 🏗️ Architecture

<!-- placeholder: mermaid diagram -->

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full story.

---

## 💡 Why this exists

Most personal-knowledge tools either:
- **Record** but don't **synthesize** (raw transcripts pile up)
- **Synthesize** but lose **personal context** (generic answers about your own meds / projects / history)
- **Inject personal context** but leak it into the **public index** (your RAG now has your address in it)

This project separates *mechanism* (system provides) from *content* (you provide) at every layer, so you can safely share the engine without sharing yourself.

---

## 🤝 Contributing

PRs welcome once we hit `v0.1.0`. For now:
- Issues for bugs / design questions — yes
- Feature PRs — wait for v0.1.0 tag
- Docs / typo PRs — always yes

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 📜 License

[MIT](LICENSE) — do what you want, no warranty.

---

## 🙏 Acknowledgments

Built on:
- [OpenWebUI](https://github.com/open-webui/open-webui) — the chat frontend
- [Qdrant](https://github.com/qdrant/qdrant) — vector DB
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) + [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) — embeddings + reranking
- [OpenRouter](https://openrouter.ai) — model routing (Claude / Gemini / etc.)
