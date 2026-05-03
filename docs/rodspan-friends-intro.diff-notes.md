# Friends-intro draft diff notes — 2026-05-04 overnight

## Two drafts written

| Audience | File | Words approx | Voice register |
|---|---|---|---|
| Cherry-Studio-adjacent power users (don't know Rodc personally; need Path A wedge framing) | `docs/rodspan-friends-intro-cherry-audience.draft.md` | ~1300 | Technical-credible founder note, like writing to peers in r/selfhosted or HN-tech crowd |
| Friend cohort already invited to alpha (know Rodc; may not know what Cherry Studio is) | `docs/rodspan-friends-intro-friend-audience.draft.md` | ~1100 | Founder-note register, more personal, less competitor-positioning |

## Structural anchor preserved from original `rodix-friends-intro.md`

Both drafts preserve:

- The 8-word canonical pitch ("ChatGPT remembers your name. Rodspan remembers your thinking. / That's the whole thing.")
- The 4-fold incumbent critique (black-box / wrong-and-can't-fix / locked / not-actually-yours) followed by the 4-fold Rodspan opposite (white-box cards / cross-model / active recall / real export)
- The "Why this exists" personal narrative (heavy AI user / 2-3h/day / two things noticed / Gemini corporate-secretary failure)
- The "Three things. That's it." structure (cards / active recall / cross-model + export)
- The "Who's it for" + "Who's it not for" anti-target structure ("ChatGPT's fine for restaurant questions")
- The Sept 3 / Sept 19 / Oct 4 side-project example (verbatim — it's the friends-intro author's own decision, not interchangeable)
- "I killed the project that night. (I might restart it next year. That's fine. Different decision.)" parenthetical-as-honesty
- The honest status section (Solo, anonymous, working out of Asia, second half of a multi-year build)
- Voice principles: short paragraphs, em-dashes precise, parenthetical-as-honesty, refusal of marketing language, specific over abstract

## What's rewritten and why

### Rodspan etymology + name change acknowledgment

- Cherry-audience draft: opens with positioning ("BYO-API client with the memory layer built in") rather than name etymology. The name is incidental; what matters is product category fit.
- Friend-audience draft: includes a brief paragraph explicitly acknowledging the rename ("If you've heard the older pitch and the name was Rodix, that was the working name through April. Renamed to Rodspan in early May per a brand audit"). Friends will have heard the older name and need the bridge; cold Cherry-Studio readers don't.

### Path A locked (BYO-API as Phase 1 position, not deferred)

The original friends-intro reading guide explicitly told subagents *"Do not assume BYOK is part of Phase 1 strategy"* — but Path A locked 2026-05-03 with BYO-API as the Phase 1 commitment.

- Cherry-audience draft: Path A is the entire framing. Comparison table with Cherry Studio / LobeChat / TypingMind makes the BYO-API + memory wedge explicit. The "Pricing" section calls out "LLM cost is on you (your key, your bill, our $0)" as the structural choice that lets Rodspan compete with Cherry Studio's free price point.
- Friend-audience draft: Path A is briefly acknowledged in the technical section ("LLM cost is on your card (Rodspan doesn't bill for inference, only for the memory + UI layer)") but not the central framing. Friends meet Rodspan as a memory product first.

### Cherry Studio competitor framing

- Cherry-audience draft: explicit comparison table (Cherry Studio / LobeChat / TypingMind / Rodspan, with the "memory layer" row as the differentiator). Names the LLM-client category directly.
- Friend-audience draft: NO competitor framing beyond ChatGPT / Gemini / Claude memory failures. Friends don't read by category; they read by product story. Adding Cherry Studio comparison would be inside-baseball framing for an audience that doesn't need it.

### Open Core acknowledgment

Per spec essence statement, Open Core mention is "use 1-sentence max where natural."

- Cherry-audience draft: a full short section ("A note on architecture (Open Core)") because Cherry-Studio-adjacent power users care about open source heritage; the mention is positive signal in this audience. About 80 words including the sunset-clause honesty note.
- Friend-audience draft: briefer mention in the technical section ("The OSS algorithm canon (`mcp_server`, `throughline_cli`) is MIT-licensed and lives at github.com/jprodcc-rodc/throughline — you can self-host the memory layer if you'd rather"). One sentence, embedded in the License bullet. Friends know Rodc personally so the OSS heritage doesn't need positioning weight.

### "Memory layer" framing correction

The original framed Rodix as "memory layer for AI chat" — which under throughline OSS framing was correct (the OSS *is* a memory layer). Under Path A + the Open Core split, Rodspan SaaS is an *LLM chat client with a memory layer differentiator*, not a memory layer itself.

- Cherry-audience draft: opens with "**LLM chat client with a memory layer**" framing. Tagline explicit.
- Friend-audience draft: keeps the original "Memory layer for AI chat" tagline because friends meet it as such — the underlying category nuance doesn't matter to them. The category correction matters externally (HN / cold-launch) more than internally (friends).

## Why two drafts

Per spec §4.2: friends-intro audience disambiguation. The original was Q2=E mix of both audiences. The two drafts let Rodc pick:

- (a) Cherry-audience as primary voice oracle → friend-audience version becomes a personal email Rodc sends to specific friends
- (b) Friend-audience as primary voice oracle → Cherry-audience version becomes the basis for HN / cold-launch / about-page (post-§A.3 marketing rewrites)
- (c) Merge — Rodc takes the friend-audience structure, lifts the Cherry Studio comparison + Path A + Open Core sections into it
- (d) Reject both, write from raw Rodc voice samples (Twitter / journal / personal writing) — option per spec §4.2 voice authenticity caveat

The drafts cannot pick option (d) for Rodc. The voice authenticity disclaimer at the top of each draft surfaces this caveat explicitly.

## Original `docs/rodix-friends-intro.md` retained unchanged

Per spec instructions, the original Rodix friends-intro stays at `docs/rodix-friends-intro.md` unmodified. It remains the canonical voice oracle until Rodc picks/merges between the two new drafts.

After Rodc lock:
1. Rename selected draft to canonical `docs/rodspan-friends-intro.md` (drop `.draft.md` suffix)
2. Optional: archive `docs/rodix-friends-intro.md` to `docs/rodix-friends-intro-pre-rename.md` for historical record
3. Unblock §A.3 marketing rewrites (per spec §2.0 dependency graph: §A.2 friends-intro lock blocks §A.3 marketing)

## What I (CC) flagged but didn't change

- Voice authenticity ceiling (spec §4.2 caveat) — both drafts inherit CC's interpretation of Rodc voice, NOT Rodc's true voice. Disclaimer at top of each draft surfaces this.
- "Public launch: weeks, not months" — same as original. Now arguably "weeks" is shorter than before since we're 5+ days into the rename overnight, but the friends-intro doesn't have a date stamp; "weeks" remains accurate framing.
- "Phase 1 = English-speaking international, no Chinese market, no EU" — spec language carries over but neither draft says it explicitly. The friends-intro context handles geo through anti-target ("ChatGPT's fine") rather than hard scoping language.

## Stage-2 review trigger (per spec §13.7)

When §A.2 lock + §A.3 first marketing draft complete, run cross-file consistency review:
- Voice samples in voice-guide.md §5 should reflect the locked friends-intro voice
- Marketing copy in landing/HN/Twitter should not contradict friends-intro framing
- If Rodc reverses any §A.2 framing decision, the cross-file review catches drift
