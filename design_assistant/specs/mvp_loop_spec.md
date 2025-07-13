# 📄 Spec — Nail the MVP Loop

## 🎯 Goal
Deliver the first full end-to-end Enso design session — where users can start a conversation, move seamlessly through three AI agents, and walk away with a polished Clarity Capsule they can reference, share, or build from.

---

## ✅ Core Features

### 1. Smooth Agent Transitions (Coach → Strategist → Evaluator)

**Why it matters:**
Contextual handoffs are key to making the multi-agent system feel intelligent, intentional, and human.

**User Experience Requirements:**
- Each handoff should include:
  - A short transition phrase in the transcript (e.g. "Let's bring in your strategist...")
  - A fade/pulse animation or subtle agent orb transition
  - Updated visual agent label (e.g. "Now speaking: Strategist")

**Code Notes:**
- Use a centralized `currentAgent` variable for transitions
- Animate UI changes with `useEffect` on agent switches

---

### 2. Clarity Capsule Generation + Export

**Why it matters:**
This is the user's *takeaway artifact* — the summary that makes their thinking tangible and portable.

**Contents:**
- "How Might We..." statement (structured from user input)
- Bullet-pointed solution concept
- Evaluator feedback: strengths, blindspots, recommendations
- Action Plan: 2–4 clear next steps

**Actions Available:**
- 📋 Copy as Markdown
- 💾 Download as `.md` or `.pdf`
- 🔗 "Send to Notion" (or simulated export until integration is ready)
- 📁 Save to local design journal

**Visual:**
- Calm, minimal card layout
- Use soft shadow, rounded corners, and generous spacing

---

### 3. Polished Start Screen + Brand Expression

**Why it matters:**
First impressions set the tone — the intro screen should reflect Enso's calm, editorial, voice-first philosophy.

**Design Requirements:**
- Centered Enso logo with ambient gradient background
- One-line mission headline:
  _"Talk to Enso. Think better. Leave with clarity."_
- Subhead:
  _Your voice-first design assistant for creative breakthroughs._
- CTA:
  🎙️ `Start Your Session` button

---

## ✅ Complete When...

- [ ] Coach, Strategist, Evaluator all live in the flow
- [ ] Transitions feel fluid and helpful
- [ ] Clarity Capsule auto-generates and is exportable
- [ ] Start screen reflects visual identity + is production-ready 