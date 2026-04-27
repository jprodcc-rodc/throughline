# Reflection Layer — design

**Status (2026-04-28):** v0.3 in progress. **Engineering gate
cleared at 0.975 pairwise clustering accuracy on author's vault**
(target was ≥75%). All three MCP tools real implementations
(`find_open_threads` / `check_consistency` / `get_position_drift`)
reading state files written by `daemon/reflection_pass.py`.
Reflection Pass orchestrates an 8-stage pipeline; stages 6
(LLM contradiction judgment) and 7 (LLM drift segmentation) remain
stubs — tool surfaces work without them, the host LLM does the
last-mile semantic judgment in conversation.

For implementation details see
[`docs/POSITION_METADATA_SCHEMA.md`](POSITION_METADATA_SCHEMA.md)
§ "Implementation milestones".

**Why this doc exists:** the Reflection Layer is throughline's core
differentiator post-v0.2.x. This doc explains what it is, what it
isn't, and why it's a different category of product than the
"AI memory" features shipping in Claude Desktop / ChatGPT memory /
mem0 / Letta / OpenMemory MCP / etc.

---

## The empty niche

By April 2026 the AI memory space is full:

- **Claude Desktop** ships native past-chat referencing
- **ChatGPT** has had built-in memory since 2024
- **mem0 / Letta / Mem0Mcp / mcp-memory-service / Hindsight / MemPalace**
  all expose MCP memory tools

What they all share:

- **Treat memory as raw text storage** — embed, store, retrieve
- **Optimize for retrieval accuracy** — better RAG, better reranking,
  more sophisticated knowledge graphs
- **Frame the problem as "AI agents forget"** — solving for assistant
  continuity
- **Target users: AI developers, agent builders, power users**

throughline could enter this space as another competitor doing the
same thing better. **It would lose.** Late entrant, no team, no
funding, no first-mover advantage.

The opportunity is to enter doing **something different**.

While everyone optimizes recall, **nobody is building a memory
layer that holds the user accountable to their own past thinking.**

Every existing memory tool is, in effect, sycophantic. It returns
what's relevant to your current question, agreeing with the framing
of the moment. It doesn't ask:

- *"Did you contradict yourself?"*
- *"What did you stop thinking about halfway?"*
- *"Has your position drifted without you noticing?"*

This is not because the technology is impossible. It's because the
framing of "memory for AI" has been **assistant-centric** rather than
**thinker-centric**.

throughline's bet: there is a population of users who don't want a
smarter assistant. They want **a more honest mirror**.

---

## Core proposition

> throughline is the AI memory layer that is loyal to the user's
> past thinking, not their present comfort.

This sentence does three things at once:

1. throughline is a **memory layer**, not an assistant
2. throughline serves the **user's past thinking**, not their
   present mood
3. throughline runs **counter to the AI industry's direction**

The third is what makes the niche defensible. Every other memory
product is racing to be more agreeable; throughline is the one
betting that some users want the opposite.

---

## Three sub-functions, useless alone, transformative together

### 1. Open Threads — unfinished thinking, surfaced

**The pattern.** You start reasoning about something complex.
Life interrupts. The thought is abandoned mid-sentence. Three
months later, the same topic comes up. You begin again from zero,
never knowing you almost reached a conclusion last time.

**The ND lens.** ADHD / AuDHD / late-diagnosed users experience
this at high frequency. Hyperfocus ends; threads scatter; nothing
finishes. Working memory doesn't extend beyond the session.
Time-blindness means "three months ago" is just "the foggy
past" without external anchors. A tool that surfaces unfinished
thinking on demand is not a feature — it's an executive function
prosthetic.

**What throughline does.** A background daemon scans every
refined card. It tags cards where reasoning was suspended — open
questions without follow-up, hypotheses without conclusion,
branches without resolution. These get `status: open_thread` in
metadata. When the user starts a related conversation, throughline
surfaces them via the `find_open_threads` MCP tool.

**User experience:**

> User: *"I want to think about pricing again."*
>
> Claude (calls `find_open_threads`): *"Before we dive in — you have
> two open threads on pricing:*
> *- Two months ago you stopped at 'how to handle freemium
>   conversion'. You'd analyzed to the LTV model but didn't
>   conclude.*
> *- Five weeks ago you wanted to research competitor data — that
>   research never appeared in any later card.*
>
> *Continue either, or start fresh?"*

---

### 2. Contradiction Surfacing — historical positions, held up

**The pattern.** You held position A three months ago, with
reasoning. Today you state position not-A, fluently, as if A had
never been your position. The contradiction doesn't surface
because no one tracks your positions across time.

**Why no one else catches it:**

- AI starts each session fresh; no cross-time memory
- Even AI WITH memory (ChatGPT, Claude past-chat) records *labels*
  ("user is considering SaaS pricing"), not *stances with
  reasoning*
- Even if it stored the stance, it tends to agree with your current
  position; surfacing conflict is anti-friction
- You don't remember either — that's why the contradiction exists

**What throughline does.** Each refined card stores a
`position_signal`:

```yaml
position_signal:
  topic_cluster: "pricing_strategy"
  stance: "against usage-based for early-stage SaaS"
  reasoning: ["LTV unpredictability", "churn risk", "runway concerns"]
  conditions: "early-stage, pre-PMF"
  date: "2026-01-15"
```

When the user states a new position, the `check_consistency` MCP
tool detects conflict and surfaces the historical position
**alongside its original reasoning**.

**User experience:**

> User: *"I'm going with usage-based pricing."*
>
> Claude (calls `check_consistency`): *"Before I help with
> implementation — three months ago you held the opposite position.*
>
> *The reasoning then was:*
> *- LTV math is unpredictable*
> *- Churn risk is severe in early stage*
> *- Runway can't support revenue volatility*
>
> *Has something changed that makes those reasons no longer apply,
> or is this a direction worth re-examining?"*

This isn't an attack ("you're contradicting yourself"). It's a
forced confrontation with your past thinking. The user can:

- **Reaffirm the change**: "Yes, we're past PMF, runway isn't the
  constraint anymore"
- **Recognize drift**: "...right, I'm doing the same thing again.
  This is why I built the tool."
- **Update the current position**: "You're right, I didn't think
  through those. Let me reconsider."

Either way, **the user thinks more clearly than before the
contradiction was surfaced**.

---

### 3. Drift Detection — how thinking has evolved

**The pattern.** Your views on a topic shift gradually across many
conversations. You don't notice the shift because each individual
change is small. Six months later you hold a view that would
surprise your past self, but you can't see how you got there.

**Four kinds of drift, each needing different response:**

| Kind | What's happening | Right response |
|---|---|---|
| Healthy evolution | New info → reasoning updated | None — let it run |
| Drift without reasoning | Stance moved but you can't say why | Audit the trajectory |
| Following trends | Industry zeitgeist pulled you | Watch for being captured |
| Mood swings | Different views in different states | Surface emotional inputs |

**But the user must first know drift is happening.**

**What throughline does.** Periodic analysis (daily or weekly)
clusters cards by topic, sorts within cluster by time, detects
stance evolution, generates a drift trajectory. The
`get_position_drift(topic)` MCP tool returns it.

**User experience:**

> User: *"What's my current framework for evaluating product
> ideas?"*
>
> Claude (calls `get_position_drift`): *"Your framework has gone
> through three phases:*
>
> *- 12 months ago: technical feasibility first*
>   *("no technical moat = no product")*
> *- 6 months ago: market size first*
>   *("a small market however deep can't sustain a team")*
> *- 3 months ago: founder-market-fit first*
>   *("only people who actually care can survive pre-PMF")*
>
> *Each shift had reasoning behind it. Most recent: heavy weight
> on founder-market-fit. Use that, or revisit the trajectory?"*

For ND users specifically — who often experience their own
cognition as inconsistent or unreliable ("I keep changing my
mind", "what I just said I don't even believe now") — this is
**metacognitive infrastructure**. An external record of intellectual
evolution becomes an anchor:

- *"I'm not flaky — my thinking is changing, with reasoning. It's
  a continuous process, not random."*
- *"My inconsistency isn't a defect — it's evolution that can be
  reviewed."*
- *"I don't have to pretend I always held one position — the
  evolution itself is visible and discussable."*

This respects ND cognition more than any productivity tool ever
has.

---

## Why all three together

### Each alone fails

- **Open Threads alone** → too niche; "AI reminds me of
  half-thoughts" isn't the core need for most users
- **Contradiction alone** → feels like attack; "I changed my mind,
  leave me alone" is a valid reaction
- **Drift alone** → occasional curiosity, not daily tool

### Together — coherent product philosophy

> "throughline is loyal to your past thinking, not your present
> comfort."

When contradiction surfaces, **alongside the original reasoning +
drift trajectory** — the user sees a complete view, not an attack.

When an open thread surfaces, **inside its topic's drift
trajectory** — the user sees the thinking lineage, not a
"forgot-about" reminder.

When drift is shown, **with each transition's reasoning** — the
user sees a thinking arc, not "I'm flaky".

**All three share one infrastructure:** topic clustering + position
metadata + temporal tracking. Build the foundation once; three
features run.

---

## Difference from Claude Desktop's "never lose the thread" feature

April 2026: Anthropic ships *Claude never loses the thread* — past-
chat referencing in the Claude Desktop app, based on chat search
+ memory synthesis (foundation in place since August 2025).

External observers might assume throughline's Open Threads has
been obsoleted. **It hasn't.** Different architectural classes:

### What Claude Desktop's chat memory does

- **Memory synthesis** — every 24h, auto-builds a user profile
  (who you are, what you do, preferences, recurring topics)
- **Chat search** — when the user asks, an LLM-side
  `conversation_search` tool retrieves past conversations
- **Reference past chats** — finds 5 relevant past conversations
  and lists them
- Typical user prompt: *"Back from PTO, where did I leave off?"*

### What Claude Desktop's chat memory does NOT do

- Doesn't identify thinking states (unfinished vs concluded vs
  superseded)
- Doesn't proactively surface anything (user must ask)
- Doesn't distinguish *facts* from *reasoning*
- Doesn't store reasoning chains; stores facts / preferences /
  decisions (industry consensus per multiple analyses, e.g.
  XTrace)
- Doesn't cross AI tools (locked to Claude)
- Doesn't detect contradictions during conversation

### What throughline Open Threads does

- **Background daemon scans proactively** — no user prompt needed
- **Identifies thinking states** — open questions without follow-up,
  hypotheses without conclusion, branches without resolution
- **Tags `status: open_thread`** — written into card metadata
- **Surfaces proactively** when the user starts a related
  conversation: *"Two open threads on pricing"*

### Side-by-side

| | Claude Desktop chat memory | throughline Open Threads |
|---|---|---|
| Trigger | Reactive (user asks) | Proactive (daemon scans + surfaces) |
| Object | Conversation snippets (text) | Thinking states (reasoning posture) |
| Capability | "Find related conversations" | "Find unfinished thinking" |
| Data ownership | Anthropic servers | User's local vault |
| Cross-tool | Locked to Claude | Vault works across all AI tools |

### One-line distinction

- Claude Desktop remembers **what you said**
- throughline knows **what you stopped thinking about**

In a user's head, these are different needs. The market has
been blurring them — that's exactly throughline's differentiation
window. No product is yet doing thinking-state tracking.

### Why this difference holds across Anthropic's likely roadmap

Anthropic will deepen memory features. But throughline has structural
advantages they're unlikely to copy:

1. **Vault as source of truth.** Anthropic won't make Claude memory
   work across OpenAI / Google / xAI tools. throughline's vault
   is naturally cross-tool.
2. **Local-first.** Anthropic's memory lives on their servers.
   throughline lives on the user's machine. For users with medical
   complexity, ND, or high privacy needs, this is load-bearing.
3. **Proactive vs reactive.** Anthropic optimizes for "ask first,
   answer second" because over-eager surfacing annoys most users.
   throughline's target users *want* proactive surfacing — their
   working memory isn't enough; they need external prompts.

The differentiation window is plausibly 1-3 years, not 5-10. In
that window throughline's job is **narrative clarity** — making
sure anyone who saw the Anthropic feature can immediately see why
throughline is a different thing.

---

## Underlying architecture

Three subsystems share infrastructure. Building any one requires
building the foundation for all three.

### Foundation: topic clustering with position metadata

Each refined card stores not just content but stance:

```yaml
content: "..."
position_signal:
  topic_cluster: "pricing_strategy"
  stance: "in favor of value-based"
  reasoning: ["customer LTV math", "competitor data", "early-stage runway"]
  open_questions: ["how to handle freemium conversion?"]
  superseded_by: null
  contradicts: []
temporal:
  conversation_id: "..."
  conversation_date: "2026-01-15"
  position_evolution_node: 3   # third card on this topic
```

Topic clustering is the hard part. Cards must group reliably:

- Same topic, different wording → same cluster
- Adjacent topics that look similar → different clusters
- Topic boundaries that shift over time → tracked correctly

Hybrid approach: **embedding similarity (bge-m3) + LLM judgment for
boundary cases**. Failure here cascades to all three sub-functions.
This is why the engineering gate is "≥75% accuracy on author's
vault before shipping the daemon" — a less-accurate clustering
produces false-positive contradictions, which kill user trust on
the first occurrence.

### Reflection Pass daemon

Runs periodically (daily or weekly), not realtime:

- Cluster cards by topic
- Identify open questions still unresolved
- Detect position contradictions across cards
- Compute drift trajectories
- Write results to card metadata

Realtime tools query the precomputed metadata — no LLM cost on the
hot path.

### MCP tools (user-facing)

```python
@mcp.tool()
def find_open_threads(topic: str | None = None) -> list:
    """Find unfinished thinking on a topic the user may want to
    resume.

    Call this when:
    - User starts a new conversation on a familiar topic
    - User asks "what was I thinking about X?"
    - User seems to be re-starting reasoning that may have already
      begun
    """

@mcp.tool()
def check_consistency(statement: str) -> dict:
    """Check whether a user's stated position contradicts their
    past positions.

    Call this when:
    - User expresses a clear position, decision, or commitment
    - User uses phrases like "I think", "I've decided", "my view
      is"
    - User seems to be making a significant choice
    """

@mcp.tool()
def get_position_drift(topic: str) -> dict:
    """Show how the user's thinking on a topic has evolved over
    time.

    Call this when:
    - User asks about their "current framework" or "current view"
    - User wants to see thinking history
    - User seems uncertain whether their view has changed
    """
```

Tool descriptions are not documentation — they are the product's
trigger surface. Description quality determines whether the host
LLM (Claude / Cursor / Continue.dev / etc.) actually fires them
in real conversations.

---

## Engineering risks (from `private/MCP_SCAFFOLDING_PLAN.md` § 7)

**1. Topic clustering accuracy (gating).**
Reflection Layer's value collapses if clustering misfires →
contradiction false-positives → user loses trust → feature is dead.
Mitigation:

- Author's vault as ground truth (existing: 2,300+ refined cards)
- Don't ship below 75% accuracy
- Hybrid embedding + LLM-judgment
- Boundary cases get last-mile LLM judgment

**2. Host LLM not calling tools.**
Tool description has to be good enough that Claude / Cursor /
Continue actually fire them at the right moment. Mitigation:

- Tool descriptions iterated as product copy, not docstrings
- Test calling rate across different prompt styles in conversations
- Optionally surface suggestions in system prompt at install time

**3. False-positive contradictions.**
Even with 80%+ clustering accuracy, edge cases trigger spurious
"you contradict yourself" calls. Mitigation:

- **Soft mode** (default): contradictions surface as questions
  ("does the earlier reasoning still apply?"), not assertions
- Optional **hard mode** for users who want stronger pushback
- Per-call user feedback ("not a contradiction") logged so the
  system improves

---

## Why this wins in 2026

1. **The market is fatigued by sycophancy.** GPT-4o's April 2025
   sycophancy regression and rollback was a turning point. Power
   users add "be brutally honest" to system prompts. They want a
   counterweight. throughline offers it structurally, not as a
   prompt hack.

2. **Memory is becoming commodity.** By April 2026, basic AI
   memory (store, embed, retrieve) is solved by ten products
   including Claude itself. The next frontier is what memory does
   *with* what it stores. throughline is among the few defining
   that frontier.

3. **Neurodivergent users are an underserved high-intensity
   market.** ADHD / AuDHD / late-diagnosed users are extremely
   loyal to tools that genuinely understand their cognitive
   patterns. They are also a growing market: late diagnosis is
   increasing globally; English-speaking ND communities are
   highly networked. They will discover and recommend tools that
   respect their actual experience.

4. **The "neurodivergent thinking compounds in AI age" narrative
   is open.** No product in the AI memory space is building from
   this angle. Every other product targets developers building
   agents. throughline targets the person whose brain works
   differently and who deserves a tool that respects how they
   think — not just remembers what they say.

---

## Path to ship

Phase 1 (shipped, v0.2.x): MCP server + 3 basic tools
(save_conversation / recall_memory / list_topics) + cross-platform
client setup. The foundation that lets the Reflection Layer plug
into any MCP-aware host.

Phase 2 (v0.3, this design): Reflection Layer.

- Topic clustering on author's vault → ≥75% accuracy → gate
- Position metadata schema in card frontmatter
- Reflection Pass daemon
- 3 new MCP tools (`find_open_threads` / `check_consistency` /
  `get_position_drift`)
- Tool description iteration against real Claude / Cursor /
  Continue.dev sessions

If the clustering gate doesn't clear, the Reflection Layer doesn't
ship. throughline's existing v0.2.x value (the OpenWebUI Filter
form, the basic MCP tools, the vault as portable source of truth)
holds either way — but the Track B differentiation window narrows.

If it does ship, throughline occupies a position no other AI memory
product is building toward. The "more honest mirror" is durable
because it cuts against the industry's training direction, not
just its product direction.

---

## What this doc is not

- Not a marketing pitch — internal positioning + public design
  rationale
- Not a sprint plan — engineering details land in
  `private/MCP_SCAFFOLDING_PLAN.md` and per-phase task breakdowns
  as Phase 2 starts
- Not a commitment to ship — clustering accuracy gate is real

---

## Final note

throughline's path is not "compete with Claude Desktop / mem0 /
OpenMemory on their terms." That's a losing path.

throughline's path is to **redefine what AI memory is for**. Not
for assistants. Not for agents. For **thinkers who deserve to be
remembered honestly, including by themselves**.

A smaller market than mem0's. But a market where, today, throughline
is alone.
