# Contributing

Thanks for the interest. This is a personal project first, open-source second — meaning the reference implementation is running 24/7 against one user's real data, and changes need to not break that.

## Before you start

- **Pre-v0.1.0**: feature PRs are held until I tag `v0.1.0`. Until then, the API and file layouts may change without notice. Please open an **issue** first for anything bigger than a typo.
- **Bug reports**: please include steps to reproduce, your OpenWebUI / Qdrant / Python versions, and a redacted badge line if RAG-related.
- **Docs / typos**: always welcome, merge fast.

## Scope guidance

What belongs here:
- Filter / daemon / RAG-server improvements
- New RecallJudge prompt variants with test fixtures
- Adapters for other vector DBs, chat frontends, or LLM routers
- Localized prompt files under `prompts/<lang>/`

What doesn't:
- Personal vault content (keep that in your own repo)
- Hardcoded personas or identities in prompts (must be swappable via config)

## Running tests

```bash
# placeholder until Phase 5
pytest
```

## PR checklist

- [ ] Ran existing tests locally
- [ ] Added tests for new behavior
- [ ] No real API keys, emails, or vault paths in the diff
- [ ] `README.md` / `docs/` updated if behavior visible to users

## Code of conduct

Be decent. Technical disagreement is fine; personal attacks are not.
