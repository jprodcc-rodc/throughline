# How Rodix Actually Works

Three things. That's it.

## 1. You talk; Rodix listens

The input model is: open the chat and type, the way you'd type into ChatGPT. No special syntax, no tags, no "save this" buttons. If you have something on your mind, write it. The conversation runs through whatever AI model is configured (Phase 1 is Anthropic's Claude Haiku 4.5 via OpenRouter; cross-model expands post-launch). The reply comes back. So far this is normal AI chat.

What's different: while the conversation runs, Rodix is doing one extra pass in the background. After your message, an extraction step looks at what you said and decides whether it's *thoughtful* (a worry, a goal, a decision in motion, a question you're chewing on) or *passing chat* (a quick fact lookup, a hello, a one-shot task). Only the thoughtful ones generate cards. If your message is "what's the capital of Mongolia," nothing happens. If your message is "thinking again about whether to leave the consulting job," that's a card.

## 2. Cards have four fields, in your own words

Every card has the same shape:

- **Topic** — what you're thinking about
- **Concern** — what worries you, what's hard
- **Hope** — what you want, where you're going
- **Question** — what's still unresolved

The extractor is built to use *your own wording*, four to eight words per field. It does not paraphrase, and it does not invent. If you didn't name a concern, the concern field is empty. **Empty is correct.** A card with two filled fields and two null is the product working — you said two things, the extractor captured those two things, the rest stayed null. Filling in plausible-looking content from imagination is the failure case Rodix refuses to ship.

This is the entire memory model. There are no hidden tags. No inferred persona labels. No shadow profile. The Vault tab shows every card you've generated, in reverse-chronological order, fully editable and deletable. If a card got something wrong, you can fix it. If you don't want it, delete it; deletion also removes it from future recall.

## 3. When topics return, Rodix brings them back

This is the part current "memory" features structurally can't do, and it's where Rodix earns its keep.

When you start a new conversation, before the AI generates a reply, Rodix searches your past cards for things that overlap with what you just said. If something relevant scores above threshold, it gets injected into the AI's context. The AI sees your real history — not a vendor's compressed guess about who you are. When the AI references one of those past cards in its reply, you'll see a small **⚡ "I brought this back"** callout below the message, naming which card was used. You can click through to see the original, mark it as relevant or not, or skip it.

The verb is "bring back." Not "surface," not "personalize." Surface is engineering language; personalize is what ChatGPT does with your name. Bring back is what Rodix does with your thinking — at the moment it matters, with a visible receipt.

## 4. Around five cards, Rodix may notice a thread

Once you have a few cards on the same loose theme, Rodix may surface a brief observation: *"I noticed a thread — here are three cards from the past few weeks; reading them together, the pattern looks like X."* This is the first-insight surface, and it's deliberately rare. Frequency is capped, sensitivity-checked, and easy to dismiss. It's not a daily summary, not a streak counter, not "your weekly Rodix wrap." If the synthesizer isn't confident enough that the thread is real, it surfaces nothing. Null over noise.

## 5. Export is one click → markdown → your hard drive

Settings has an Export button. One click produces markdown files: one per card, plus an index. Open them in Obsidian, paste into Notion, throw them on a USB stick, run them through your own scripts. The actual ownership story is markdown export; that's the artifact you can verify is yours without trusting Rodix's UI.

(Storage is server-side, by the way — so this is not zero-knowledge encryption, and won't pretend to be. Encryption hardening is on the post-launch roadmap. The Privacy Summary names what's actually true today.)

## A worked example

Last Tuesday. I'd been turning over whether to keep building a side project for two months. Talked to AI about it maybe a dozen times across two providers, plus my wife, plus a friend on a walk.

I opened Rodix and said: *"Thinking again about whether to kill the side project."*

Three cards came back, dated September 3, September 19, October 4:

```
[Sept 3]
Topic:    Side project shutdown
Concern:  Sunk cost — 200 hours in
Hope:     Reclaim 6 hours/week
Open:     Is the metric "hours" or "joy"?

[Sept 19]
Topic:    Side project shutdown
Concern:  I'd miss the craft of it
Hope:     A clearer signal that it's worth continuing
Open:     What signal would change my mind?

[Oct 4]
Topic:    Side project shutdown
Concern:  Stuck on the same fence for 6 weeks
Hope:     Just decide
Open:     What does "stuck" tell me?
```

Reading the three back-to-back, the pattern was suddenly obvious in a way it never was inside any single conversation. I kept moving the bar — September 3 it was hours, September 19 it was a signal, October 4 it was just-decide. I wasn't actually torn. I was avoiding the decision.

That's the kind of insight you can't get from any one conversation. You can only see it from the spine of conversations, which is what cards give you and what no current AI tool surfaces.

I killed the project that night.

(I might restart it next year. That's fine. Different decision.)
