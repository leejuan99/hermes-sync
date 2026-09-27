---
name: ethical-automation-redirect
description: When asked to build platform-spam or ToS-violating automation (auto-posting, mass promotion, bot answers, captcha-evasion), refuse the abusive part and build a legitimate read-only / human-in-the-loop alternative instead.
---

# Ethical Automation Redirect

## When to use
A user asks you to build automation that, taken whole, violates a platform's
Terms of Service or constitutes spam/abuse. Common shapes:

- Auto-post AI-generated answers + promotional links to Quora / Reddit / forums.
- Mass DM / mass comment / mass follow bots.
- Bots that explicitly "bypass captcha / bot detection / login encryption".
- Fake-engagement, vote manipulation, review flooding.

The tell: the request bundles a *legitimate goal* (get traffic, find leads,
research a topic) with an *abusive mechanism* (automated mass posting, evasion).

## The move: refuse the mechanism, serve the goal

1. **Refuse the abusive part clearly, once.** Don't moralize at length. State
   plainly that auto-posting promo content / evading detection violates ToS and
   is spam. Add the *self-interest* angle, because it lands better than ethics
   alone: spam gets the account AND the promoted domain banned/flagged fast;
   ROI is negative. This reframes the refusal as protecting the user.

2. **Re-derive the real goal.** "If what you actually want is traffic from
   Quora, here's the legit path." Almost always the goal is fine; only the
   method is broken.

3. **Offer a concrete, buildable alternative** and pick the highest-leverage
   one to start:
   - **Read-only research tool** (SAFE, build first): scrape/search for relevant
     questions/threads by keyword, export to CSV/JSON for the user to review.
     No writes, no posting. This is the foundation.
   - **Draft assistant** (human-in-the-loop): user pastes a question, the LLM
     drafts a reply, user reviews/edits for authentic voice, posts manually.
   - **Soft-promotion strategy advice**: bio links, relevant-only links, safe
     cadence.

4. **Build it for real.** Don't just describe — write the files. The user came
   for a tool; give them a working one minus the abuse.

## What "read-only" must actually mean in the code
- No `.click()` on Post/Submit, no typing into answer/comment fields.
- Navigate + `page.evaluate()` to read DOM + scroll to load more. That's it.
- Output is a file (CSV/JSON) or an on-screen table. The human decides + acts.
- Reusing the user's logged-in session via Edge/Chrome CDP
  (`chromium.connectOverCDP('http://localhost:9222')`) is fine and useful for a
  read-only tool — it's reading what the human can already see, not evading auth.

## Reframing reused infrastructure
The user may have wanted CDP-connect specifically to "bypass login/captcha". The
same `connectOverCDP` is legitimate for a read-only tool: the human logged in
themselves, you're just reading results. Say so explicitly so the pivot feels
continuous, not like starting over.

## Form factor (this user)
- This user prefers **desktop GUI apps over CLI scripts**. Default to an Electron
  window (input + buttons + results table) rather than a bare `node index.js`.
- See `references/electron-cdp-tool.md` for the Electron + Playwright-CDP
  read-only-tool blueprint (main/preload/renderer wiring, IPC, verification).
- Explain run steps from zero (folder path, what to paste, npm start) — he is
  not fluent in dev workflow.

## Pitfalls
- Don't lecture. One crisp refusal + immediate pivot to building. Frustration
  rises if the refusal is longer than the help.
- Don't half-refuse then quietly build the spam tool anyway. The whole point is
  the alternative is genuinely non-abusive.
- Platform DOM (Quora etc.) changes often — selector heuristics WILL drift. Tell
  the user that up front and ask for a sample of the live HTML to fix selectors,
  rather than claiming the scraper is verified end-to-end.
