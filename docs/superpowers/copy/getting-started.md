# Getting Started

This is not a tutorial. It's a pattern most heavy AI users settle into in the first week or two — share it as a rough map, take from it what's useful.

## Day 1 — Just open it and talk

Don't think about what Rodix is "for." Don't try a test query to see if extraction works. Open the chat and bring a real thing — a decision you've been turning over, a worry, a project that's been stuck, a question you keep meaning to think through. Talk to it the way you'd talk to ChatGPT or Claude.

After your first thoughtful message, a card may appear in the Vault. Glance at it. Don't grade it; just notice it's there. If it looks wrong, leave it for now — Day 2 is for editing.

The first-day failure mode is treating Rodix as a demo. The cards generated from "test, please extract this" prompts are not useful. The cards generated from "I don't know whether to take the new role" are.

## Day 2–3 — Notice what's there. Edit one.

Open the Vault. Read what's accumulated — usually one to three cards if Day 1 had one or two real conversations.

Pick one card and see if the four fields match what you actually said. The extractor uses your own wording, four to eight words per field, and leaves fields null when they're not present in the message. If a card has only a topic and an open question — that's correct. If a card invented a concern you didn't voice, fix it. Click the field, edit, save. The point of Day 2 is to confirm the white-box claim is real: what's there is what you said, and you can correct it.

If a card is genuinely off, delete it. Deletion is the right move sometimes; Vault size is not the score.

## Day 4–7 — Come back. Look at the spine.

This is when the value starts to show, or doesn't.

Open Rodix and continue something you wrote about earlier in the week. When you do, watch for the **⚡ "I brought this back"** callout below the AI's reply — that's recall firing, with a visible link to the card it brought into context. The first time it fires on something genuinely relevant, the mechanism clicks: the AI didn't have to be re-explained the backstory, because Rodix carried it across.

Open the Vault tab and scroll. With four to eight cards on a few different topics, you start to see the shape of what you've been thinking about — not as a stream of conversations, but as a structured record. Some cards will pair up; some will surprise you. Some you'll want to delete in retrospect, which is also fine.

## Week 2 — Keep going. The compounding kicks in around Day 7–10.

The pattern most heavy AI users find: the first week is "Rodix is interesting." The second week is when you actually catch yourself thinking *"oh, I covered this already"* and pulling up the past card to continue rather than re-explaining. Around Day 7–10, with twelve to fifteen cards across a handful of recurring topics, the spine of your thinking starts to be legible to you in a way single conversations never made it.

This is also when the first-insight surface may fire — at around five cards on a loose theme, Rodix may surface a brief "I noticed a thread" observation. It's deliberately rare. If it doesn't fire, that's the synthesizer being honest about not having enough signal yet, not a bug.

## What to skip

- **Don't try to organize the Vault.** It's not a notes system. There are no folders, no tags you assign, no project structure. The cards organize themselves around the topics you actually keep returning to.
- **Don't write into it.** Rodix doesn't have a "create card" button. If you want to write a note, write a note in your notes app. Cards are a byproduct of conversations, not a destination.
- **Don't grade extraction quality on Day 1.** The pipeline is calibrated against an 80-case eval set with a 2.3% hallucination cap, but on individual messages you'll see variance. Edit, delete, move on. The extractor learns nothing from your edits in Phase 1, but you still have full control of the artifact.

## What to expect

Sparse cards are normal — a card with two filled fields and two null is the product working correctly. Recall will not fire on every message; it fires when something actually overlaps. Some thoughtful messages won't generate a card if extraction couldn't find a clear topic. None of this is a degraded state; it's the null-by-default discipline that keeps the Vault from filling with invented content.

If after two weeks of regular use you don't feel any compounding — the cards aren't useful, recall doesn't help, the spine isn't legible — the wedge probably isn't for you, and that's a real outcome. ChatGPT's fine for a lot of use cases. Rodix is for a specific one.

If it does compound, the tax-paying re-explanation you've been doing for the past year of heavy AI use will start to feel less like work.
