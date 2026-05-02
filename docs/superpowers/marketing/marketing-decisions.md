# Marketing Decisions Log — Tier 2 Task 6

**Author:** marketing-suite-architect
**Date:** 2026-05-03
**Scope:** Type-B decisions made autonomously while drafting the 5-channel marketing suite. Type-A escalations (those needing Rodc decision before launch) are flagged at the end.

---

## Type-B decisions (made and logged, no escalation needed)

### D1 — Founder essay separator style: three-asterisk scene-breaks, NOT "Part 1 / 2 / 3" headings.

**Why:** Founder-narrative-arc.md adaptation note explicitly allows this: *"Section breaks remain; 'Part 1 / 2 / 3 / Closing' headings can be removed in publish version (replace with one-line scene-breaks or three-asterisk separators) since friends-intro itself uses no part-headings."* Friends-intro prose has no part-headings; the essay should publish in friends-intro shape, not academic-paper shape.

**Trade-off considered:** Part headings would help skim-readers navigate. But the essay is friends-intro register — friends-intro is read end-to-end or not at all, and the pull-quote-able sentences (8-word pitch, "I killed the project that night," "ChatGPT's fine") are the actual navigation aids.

### D2 — HN post body uses sub-headings ("How it actually works:" / "What I'd flag honestly before you sign up:") — NOT prose flow.

**Why:** HN audience has different reading patterns than friends-intro audience. HN readers skim for mechanism + limits before deciding to engage. Sub-headings + bullet lists are HN-shaped, while prose flow is essay-shaped. The voice register is identical (anti-spin, refuses-to-dramatize, parenthetical-as-honesty); only the structural delivery shifts.

**Trade-off considered:** prose flow would be more friends-intro-faithful at the surface level. But HN voice is friends-intro at scale-of-paragraph, not at scale-of-document. HN readers are pattern-matching the post structure as well as the voice; matching only the voice while violating the structure is anti-pattern.

### D3 — PH first comment is friends-intro register full-strength, NOT compressed PH-shaped.

**Why:** The PH first-comment is the founder's voice on the product page. It's the only place a PH visitor will read more than 60 chars of Rodc's words; under-investing here loses the voice signal entirely. 389 words is on the long end of PH first-comments but acceptable — the comment ends with a link to the founder essay for readers who want more.

**Trade-off considered:** A 150-word PH-typical first-comment would conform to platform norms. But PH is full of conformist first-comments; Rodix's distinctiveness is the voice itself, and a 150-word reduction would dilute the voice without saving meaningful reader time.

### D4 — Twitter thread length: exactly 8 tweets, not 6 and not 10.

**Why:** Founder-narrative-arc adaptation note: *"Eight tweets total feels right."* Validated against the structural breakdown — 1 hook + 6 substance + 1 invitation = 8. Six tweets compresses too aggressively (loses the structural-insight tweet); ten tweets dilutes (each tweet's hammered-fragment cadence depends on each carrying a complete claim; padding kills the cadence).

**Trade-off considered:** longer threads (15-20 tweets) get more impressions in Twitter's algorithm but read as marketing-effortful. Shorter threads (5-6) read as efficient but lose the cumulative structural argument. 8 is the friends-intro paragraph count compressed to tweet form.

### D5 — Twitter signature is `@rodix` handle only, NOT `@rodix · Rodc, building from Asia`.

**Why:** Anonymous-founder constraint per brand book §3 / position-strategy §6. The Twitter thread itself signals authorship via tweet 1's pitch + the friends-intro voice; an explicit founder-tagline signature would tilt toward LinkedIn founder-coach drift. Founder essay and PH first-comment can carry the "— Rodc" sign-off because those surfaces support a longer voice signal; Twitter signature should stay clean.

**Trade-off considered:** signing every tweet with "— Rodc" would build founder-recognition over time. But Rodix is specifically anonymous Phase 1; over-signing teaches the audience to expect a personal-brand reveal that isn't coming.

### D6 — Video script is voiceover-only, NOT founder-on-camera.

**Why:** Anonymous-founder constraint, hard-locked. Rodc cannot appear on camera at Phase 1 launch. Voice-only is structurally aligned with friends-intro register — the friends-intro is a written voice, and translating to spoken voice without adding a face preserves the intimate-but-distanced register the brand depends on.

**Trade-off considered:** founder-on-camera videos perform 2-3x better on Twitter / YouTube engagement metrics. Worth nothing if the founder is anonymous. Phase 2 may revisit this if/when Rodc decides to drop anonymity, but Phase 1 is locked.

### D7 — Music recommendation: 3 options ranked, A primary (Aphex Twin "Avril 14th" reference, royalty-free swap suggested).

**Why:** Brand book §6 anti-Granola "handwritten warmth" anti-spec applies to music selection too. The Aphex Twin / Nils Frahm / William Tyler register is restrained, late-night, considered-terrain — matches Explorer brand archetype. Hans-Zimmer-epic / Explosions-in-the-Sky-build / M83-tech-founder-hype registers are explicitly avoided.

**Trade-off considered:** royalty-free music platforms have limited ambient-classical inventory; Rodc may have to compromise on track selection. The reference tracks are intentionally specific so Rodc can identify register-equivalents on Artlist / Musicbed / Epidemic Sound.

### D8 — Screenshot 2 (recall callout) honest pre-screenshot label about Wave 2.

**Why:** Brand book §7b is explicit: brand commitments stand, but the operational implementation has known string-level gaps. The recall callout copy `⚡ 我把这个带回来了` and the action-button set `用上了 / 不相关 / 已经想过 / 跳过` are brainstorm-locked but not yet shipped (Wave 1b currently renders placeholders). Marketing screenshots that show the locked target copy without a Wave 2 honesty caption would violate Decision 6 (honest about architectural compromises) — claiming what isn't shipped.

**Trade-off considered:** waiting until Wave 2 ships to capture the screenshot would delay PH launch. The compromise: capture a mock or a Wave 1b screenshot with an explicit Wave 2 honesty caption per brand book §7b. Honesty caption preserves anti-spin posture at the cost of slight visual polish.

### D9 — HN post does NOT include the killed-project anecdote.

**Why:** Founder-narrative-arc adaptation note: *"The 'I killed the project that night' example can drop in the HN compression — HN readers will pattern-match without it."* HN audience evaluates on mechanism-and-limits; the personal anecdote is essay-shaped. Cutting it for HN makes room for the technical detail (Haiku 4.5 + FTS5 bigram + threshold values) that HN readers actually want.

**Trade-off considered:** keeping the anecdote would carry the friends-intro voice more fully. But HN posts that lead with personal anecdote on technical products read as off-platform (closer to Substack than to HN). Voice consistency is preserved via the volunteered-limit triplet, the Gemini failure-mode reference, and the structural-incentive argument — all in friends-intro register, none requiring the killed-project anecdote.

### D10 — PH category: Productivity (primary) + AI (secondary), NOT "thinking tools" or "automation".

**Why:** PH taxonomy doesn't have a "thinking tools" category and forcing one would require selecting from inappropriate options. Productivity is the closest accurate fit even though Rodix is anti-engagement; AI is the truthful secondary. "Automation" / "agents" are inaccurate (Rodix doesn't automate anything), and "GPT wrapper" categorization (which PH does have a niche for) misrepresents the architectural commitment to cross-model.

**Trade-off considered:** opting out of categorization would lose discoverability. The compromise: accept Productivity even though Rodix critiques productivity-tool framing, because the alternative (no category) loses signal worse than the slight category mismatch.

### D11 — Cross-channel quote-frequency for the volunteered-limit triplet: full in 3 channels, compressed in 2 channels (none omit).

**Why:** Brand book Decision 6 (honest about architectural compromises) is the highest-stakes anti-spin commitment. Allowing any channel to omit the triplet entirely would create a surface where readers learn about Rodix without the encryption-honesty caveat. Full version in essay / HN / PH first-comment; compressed version in Twitter thread tweet 7 + video script visual caption. No surface left where the triplet is absent.

**Trade-off considered:** the Twitter thread is at 277/280 chars and adding the full triplet would cost a substantive line. The compromise: compress to one parenthetical inside tweet 7 ("Server-side recall (so this is not zero-knowledge — won't pretend to be)"), preserves the structural honesty inside the brand-book-locked sentence cadence.

---

## Type-A escalations (flagged for Rodc decision before publish)

### E1 — Founder essay publish target.

**Question:** Where does the founder essay live at launch? Options:
1. **rodix.app/founder** — own URL, owns SEO, full editorial control. Risk: requires Phase 1 site to support an essay page (needs design + dev work).
2. **Substack** — distribution to Substack readers, easy crosspost. Risk: anonymous founder + Substack-handle creation is a secondary identity decision.
3. **HN post body itself** — only as compressed HN post, no separate essay. Risk: loses long-form reader segment.

**Recommendation:** Option 1 (rodix.app/founder) if the landing-deliverable Tier 2 task is on track to support it. Otherwise Option 2 (Substack) with anonymous handle `rodix` matching the Twitter handle.

### E2 — Twitter handle decision: `@rodix` available?

**Question:** Has `@rodix` been claimed? If not, is Rodc willing to register and post from it? If `@rodix` is taken, fallback options needed: `@rodix_app` / `@userrodix` / `@rodix_io`. The marketing assets reference `@rodix`; that reference needs to be locked before publish.

**Recommendation:** Rodc to confirm or supply alternative handle before Twitter thread goes live.

### E3 — Wave 2 recall callout ship timing relative to PH launch.

**Question:** If Wave 2 ships before PH launch, screenshot 2 (recall callout) can be captured live with the brand-locked copy `⚡ 我把这个带回来了` + buttons `用上了 / 不相关 / 已经想过 / 跳过`. If Wave 2 ships after PH launch, screenshot 2 needs a mock (After Effects) or a Wave 1b capture with the honesty caption. This is a launch-timing-dependent decision Rodc owns.

**Recommendation:** PH launch should NOT slip waiting for Wave 2. Use Wave 1b screenshot with honest Wave 2 caption (per D8 above) and update PH submission post-launch when Wave 2 ships.

### E4 — Founder essay length final cut: 1,180 words (current), or expand toward 1,500?

**Question:** Founder-narrative-arc.md Part 1-3 + Closing is ~1,180 words. The brief allows 800-1,500 words. Expanding toward 1,500 would add: more detail on the see → trust → verify mechanism, more examples beyond the side-project anecdote, more on why a 4-field schema vs. free-text. Compressing toward 800 would lose the killed-project specifics or the 4-bets architectural framing.

**Recommendation:** Hold at 1,180. Friends-intro itself is ~1,350 words; staying close to friends-intro length keeps the register tight. Expanding would tilt toward "long-form essay" voice; compressing would lose structural argument.

### E5 — Video format priority — vertical 9:16 OR horizontal 16:9 if Rodc has time for only one?

**Question:** Both formats recommended in launch-video-script.md. If Rodc has bandwidth for only one production pass, which should ship first?

**Recommendation:** Horizontal 16:9 first — it's the landing-page hero asset (most-seen surface, most editorial control). Vertical 9:16 is a re-frame from the same source recordings with slight motion-graphics adjustments; Rodc can do this as a post-launch follow-up. If only ONE format ever ships: 16:9.

---

## Decisions deliberately deferred to later phases

- **Pricing copy.** Position-strategy §6 explicitly says pricing is Task 4's responsibility and position copy must leave room for whatever pricing lands. All five channels use "TBD honestly" or "weeks, not months" framing for any pricing question. No commitment to "free tier" or "paid only" framing in any deliverable.
- **Wave 2 active-recall ship copy.** The brand-locked copy `⚡ 我把这个带回来了` + buttons appears in screenshot description for screenshot 2 only. None of the five channels' body copy commits to specific recall callout strings — that's Wave 2 deliverable, not marketing copy.
- **Open source decision.** HN post and PH maker comment 5 both say "partial — recall orchestrator + extractor prompt are public, full app stack is a Phase 2 question I'm leaving open." This is Rodc's decision to harden later; current copy preserves optionality.

---

*End marketing-decisions.md. Type-B decisions: 11 logged, all defensible against the brand book and friends-intro register. Type-A escalations: 5 flagged for Rodc decision before publish. Defer-to-later: 3 explicit non-decisions.*
