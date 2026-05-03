# Rodspan Component Patterns

Sketches + props + voice-coherence notes for the canonical Rodspan UI surfaces. Visual tokens live in `visual-tokens.json`. Voice rules live in `voice-guide.md`.

---

## 1. Chat bubble (user)

```
                                        ┌──────────────────────────┐
                                        │ Thinking again about     │
                                        │ whether to kill the      │
                                        │ side project.            │
                                        └──────────────────────────┘
                                                              09:14
```

**Props:** `{ content: string, timestamp: ISO, edited?: boolean }`
**Visual:** background `surface` (`#27272a`), text-primary, padding `12px 16px`, border-radius `12px`, max-width `70%`, right-aligned.
**Voice-coherence:** user input is sacred — render exactly. No edit / paraphrase. Edited indicator is a small `(edited)` after timestamp, never a celebration.

---

## 2. Chat bubble (AI / Sage layer)

```
Around the sunk-cost worry — you said "200 hours in" but
the hours number didn't move anything by itself. The shift
was when you switched the metric from hours to joy.

That's a different decision than killing it on hours alone.
                                                         09:15
```

**Props:** `{ content: string, timestamp: ISO, model: string, is_streaming?: boolean }`
**Visual:** background transparent (no bubble), text-primary, padding `12px 0`, max-width `85%`, left-aligned. Type-first hierarchy.
**Voice-coherence:** Sage layer (per `app/web/prompts/rodspan_system.md`). Round 1 ask · Round 2 maybe · Round 3+ stop asking and reflect. Quote user's actual words back ("200 hours in" / "joy"). 2-4 sentences default. Never "Of course!" / "Great question!" openers.

---

## 3. Card with Promise (the canonical Rodspan object)

```
┌────────────────────────────────────────────── Sept 3 · GPT-5 ┐
│                                                              │
│  Topic                                                       │
│  Side project shutdown                                       │
│                                                              │
│  Concern                                                     │
│  Sunk cost — 200 hours in                                    │
│                                                              │
│  Hope                                                        │
│  Reclaim 6 hours/week                                        │
│                                                              │
│  Open question                                               │
│  Is the metric "hours" or "joy"?                             │
│                                                              │
│  ↗ Open conversation                       ✎ Edit   🗑 Delete │
└──────────────────────────────────────────────────────────────┘
   amber 1px border (#d97706)
```

**Props:** `{ id: UUID, topic?: string, concern?: string, hope?: string, question?: string, source_conversation_id: UUID, source_message_id: UUID, model: string, created_at: ISO }`
**Visual:** amber `#d97706` border 1px (this is the verification color). Surface background. Padding `16px 20px` desktop / `8px 10px` mobile. 4 named fields: topic / concern / hope / question.
**Null rendering:** Empty fields render as blank (label only, no value). Empty is correct (Decision 5). Never "N/A", never invented placeholder.
**Source link:** mandatory — every card traces to its conversation. The `↗` glyph is the only acceptable iconography for "open original."
**Voice-coherence:** Field labels per `app/web/static/copy/tooltips.json`:
- topic → *"What you're thinking about"*
- concern → *"What worries you / what's hard"*
- hope → *"What you want / where you're going"*
- question → *"What's still unresolved"*

The card is the most-photographed object in Rodspan marketing. Treat it like a museum specimen — never decorate, never animate on hover beyond a 1px border-color shift.

---

## 4. Vault list view

```
┌──────────────────────────────────────────────────────────────┐
│  Vault                                  [Search] [Filter] [⋯]│
├──────────────────────────────────────────────────────────────┤
│  Sept 3 · 2 cards                                            │
│  ┌─ Side project shutdown ─────────────────────────────────┐ │
│  │ Sunk cost — 200 hours in · Reclaim 6 hours/week         │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─ Mom's cognitive decline ──────────────────────────────┐  │
│  │ Specialist appointment in 2 weeks · Dignity vs safety  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Aug 28 · 1 card                                             │
│  ┌─ Salary negotiation ───────────────────────────────────┐  │
│  │ Asking for $20k more · Counterfactual offer in hand    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Props:** `{ cards: Card[], date_groups: { date: ISO, cards: Card[] }[], search_query?: string, filter?: { topic?: string, date_range?: [ISO, ISO] } }`
**Visual:** sticky date headers in amber accent (small caps, `0.75rem`, weight 600). Card list items use surface background, no border (border is reserved for full Card with Promise detail). One-line summary: topic + condensed concern · hope.
**Empty state:** `"Your cards will appear here as you talk to Rodspan. We don't write them — your thinking does."` (sourced from `empty-states.json`)
**Voice-coherence:** the Vault is a top-tab equal to Chat (Decision 1). Never bury it in a settings page. Search field placeholder: *"Search across topics, concerns, hopes, and open questions. Your wording, not paraphrased."*

---

## 5. Vault detail (single card focused)

Full Card with Promise component (see §3) rendered at `max-width: 640px` centered, with conversation-source preview below:

```
┌──────────────────────────────────────────────────────────────┐
│                       [Card with Promise]                    │
└──────────────────────────────────────────────────────────────┘

  Source — Sept 3, 09:14 · GPT-5 conversation                 ↗

  > Thinking again about whether to kill the side project.
  > It's been six weeks on the same fence. 200 hours in,
  > but the hours number doesn't actually mean anything by
  > itself.
```

**Voice-coherence:** Source preview shows the actual user message that produced the card. No paraphrase, no AI summary. The card's traceability is the trust mechanism.

---

## 6. Recall callout (`⚡` — the AI character speaking)

```
┌─ ⚡ 我把这个带回来了 ──────────────────────────────────────┐
│                                                            │
│  从 Sept 3 的卡片:                                          │
│  Topic: Side project shutdown                              │
│  Open: Is the metric "hours" or "joy"?                     │
│                                                            │
│  [用上了]  [不相关]  [已经想过]  [跳过]                    │
└────────────────────────────────────────────────────────────┘
   amber 1px border, faint amber tint background
```

**Props:** `{ recalled_card: Card, recall_type: 'topic'|'stance_drift'|'loose_end'|'decision_precedent', confidence: number, action_callbacks: { used, irrelevant, already_thought, skip } }`
**Visual:** amber `#d97706` border, faint amber tint background `rgba(217,119,6,0.05)`. The `⚡` glyph is the SINGLE permitted emoji in Rodspan. It is the kept-promise signature.
**Locked copy:** header `⚡ 我把这个带回来了` / English `⚡ I brought this back`. Action buttons `用上了 / 不相关 / 已经想过 / 跳过`.
**Wave 1b reality:** current implementation renders placeholder `记忆提醒 · 话题相关` with `记下了 / 看了 / 不相关 / 忽略`. Patching to locked copy is a Wave 2 deliverable on `#active-recall-base`.
**Voice layer:** This speaks AS the AI character (Sage layer). First-person mid-conversation. The verb is "bring back" / "带回来" — never "surface", never "personalize".

---

## 7. Settings modal

```
┌─ Settings ─────────────────────────────────────────────────┐
│                                                            │
│  Account                                                   │
│  Email           rodc@rodix.app                            │
│  Vault size      247 cards · 2.3 MB                        │
│                                                            │
│  ───────────────────────────────────────────────────────   │
│                                                            │
│  Memory                                                    │
│  Auto-extraction         [●─── Off ]                       │
│   Pause card extraction. Chat continues.                   │
│                                                            │
│  Recall sensitivity      [Default ▾]                       │
│   How often Rodspan brings past cards back.                  │
│                                                            │
│  ───────────────────────────────────────────────────────   │
│                                                            │
│  Export                                                    │
│  [ One click → markdown files ]                            │
│   Open in Obsidian. Paste into Notion. USB stick.          │
│                                                            │
│  ───────────────────────────────────────────────────────   │
│                                                            │
│  Account                                                   │
│  [ Delete account · 30-day SLA ]                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Voice-coherence:**
- Sectioned, not tabbed. Settings is rare-use; tabs add friction.
- Helper text under each control names mechanism, not benefit. *"Pause card extraction. Chat continues."* not *"Take control of your privacy!"*
- Export button label: *"One click → markdown files"* (per `tooltips.json`). The arrow is a Lucide chevron, not an emoji.
- Delete account is plain-text, not a red panic button. Honest qualifier: *"30-day SLA"*. Per Decision 4 + the friends-intro voice — destructive controls do not need to be dramatized; they need to be findable.

---

## 8. Onboarding 3-step

Phase 1 device priority is desktop Web primary; mobile responsive does just enough to not visibly break.

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1 of 3                                                │
│                                                             │
│  ChatGPT remembers your name. Rodspan remembers your          │
│  thinking.                                                  │
│                                                             │
│  Type something you've actually been thinking about.        │
│  Not a test — a real one. Cards will appear as you talk.    │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Type a real thought…                               │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
│                                          [Continue]         │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│  Step 2 of 3                                                │
│                                                             │
│  This is a card.                                            │
│                                                             │
│  Four fields: topic, concern, hope, open question. We       │
│  don't write them — your thinking does. Empty fields are    │
│  fine; we never invent.                                     │
│                                                             │
│  [Card with Promise mock from step 1's content]             │
│                                                             │
│  Edit any field. Delete the whole card. Open the source     │
│  conversation. It's yours.                                  │
│                                                             │
│                                          [Continue]         │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│  Step 3 of 3                                                │
│                                                             │
│  Your memory works across models.                           │
│                                                             │
│  GPT-5, Claude, Gemini — same cards, same continuity. One   │
│  click exports everything to markdown. Your hard drive,     │
│  your call.                                                 │
│                                                             │
│  Server-side recall today. Encryption hardening on the      │
│  post-launch roadmap.                                       │
│                                                             │
│                                          [Start using]      │
└─────────────────────────────────────────────────────────────┘
```

**Voice-coherence:**
- Step 1 quotes friends-intro hero verbatim. No "Welcome to Rodspan!" preamble.
- Step 1 first-chat hint is sourced from `empty-states.json` (`"Type something you've actually been thinking about. Not a test — a real one. Cards will appear as you talk."`).
- Step 2 names the 4 fields, names null-default ("we never invent"), names the 3 user controls (edit / delete / open source).
- Step 3 names cross-model + markdown + the architectural honesty (server-side today, encryption on roadmap). This is the brand stance compressed to onboarding scale.
- Total onboarding word count: under 130 words. Onboarding is not an essay.

---

## 9. Conversation list (sidebar)

```
┌─ Conversations ─┐
│  + New          │
├─────────────────┤
│ Today           │
│  Side project   │
│   shutdown      │
│                 │
│ Sept 1          │
│  Salary nego    │
│                 │
│ Aug 28          │
│  Mom's care     │
└─────────────────┘
```

**Voice-coherence:** Conversation titles auto-extracted from first user message (4-8 word verbatim, per `claim_extractor.md` discipline). Never AI-paraphrased ("Discussion about your career"). Date grouping: today / yesterday / [date]. No "1 day ago" / "2 days ago" — concrete dates only.

---

## 10. State icons (loading / error / success)

- **Loading:** Lucide `loader-2` icon with rotation animation. Label: *"Usually 2-4 seconds"* / *"通常 2-4 秒"* — show only when load > 1.5s.
- **Error:** Lucide `alert-circle` icon, error color `#ef4444`, paired with one-paragraph error message from `errors.json`. Never a modal-blocking dialog unless the error is destructive.
- **Success:** Lucide `check` icon, success color `#22c55e`, brief 1.5s toast. No celebration framing on save events. *Procedural, not festive.*

---

## Routing rule reminder

The recall callout is the only component that speaks AS the AI character (Sage layer). Everything else — error states, empty states, settings copy, tooltips, onboarding, marketing — is Rodc-presenting-Rodspan → Explorer layer.

When in doubt, write Explorer. The AI character has its system prompt as enforcement.
