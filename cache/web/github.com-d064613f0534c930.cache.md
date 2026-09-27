# tashfeenahmed/freellmapi
URL: https://github.com/tashfeenahmed/freellmapi.git

# tashfeenahmed/freellmapi

OpenAI-compatible proxy that stacks the free tiers of 28 LLM providers (~4B tokens/month) behind one /v1 endpoint — plus any custom OpenAI-compatible endpoint. Smart routing, automatic failover, encrypted keys. Personal experimentation only.

- Stars: 19281
- Forks: 2807
- Watchers: 19281
- Open issues: 73
- License: MIT License
- Homepage: https://freellmapi.co
- Default branch: main
- Created: 2026-04-21T13:38:59Z

## Languages

- CSS
- Dockerfile
- HTML
- JavaScript
- PowerShell
- Shell
- TypeScript

## Top Contributors

- tashfeenahmed (417 contributions)
- suantea (45 contributions)
- OhOkThisIsFine (18 contributions)
- jasnoorgill (9 contributions)
- nordbyte (7 contributions)
- Tazrif-Raim (6 contributions)
- danscMax (5 contributions)
- LoneRifle (5 contributions)
- kairwang01 (5 contributions)
- v0rtex1223 (4 contributions)

---

## README

 

# FreeLLMAPI

**4 billion tokens per month. 29 free LLM providers. 358 free model endpoints. One OpenAI-compatible endpoint.**

Aggregate free tiers from dozens of providers, plus custom OpenAI-compatible chat, embedding, image, and audio endpoints, behind a single `/v1` API. Keys are stored encrypted. A router picks the best available model for each request, falls over to the next provider when one is rate-limited, and tracks per-key usage so you stay under every free-tier cap.

CI
GitHub stars
License: MIT
PRs Welcome
Docker image
Ask DeepWiki

**freellmapi.co** · browse the full catalog: 251 model families, 358 free endpoints

**English** · 简体中文

 
 
 
 
 
 

FreeLLMAPI dashboard — Models page with the monthly token budget

Your router updates its own model catalog from a signed feed: new free models, quota changes, and compatibility fixes land without a `git pull`.
**Go live at freellmapi.co** ($19/yr, cancel anytime).

 

---

## Contents

- Why this exists
- Supported providers
- Compatible CLIs & coding agents
- How it compares
- Features
- Quick start
- Desktop app
- Works with OpenAI-compatible clients
- Languages
- Premium (live catalog)
- Using the API
- Screenshots
- How it works
- Limitations
- Contributing
- Disclaimer

**Guides:** Install & deploy · API reference · Clients & coding agents · Prompt compression · Architecture & internals · Documentation index · Contributor guide

## Why this exists

Every serious AI lab now offers a free tier, a few million tokens a month, a few thousand requests a day. On its own each tier is a toy. Stacked together, they add up to roughly **4 billion tokens per month** of working inference capacity, across **251 model families / 358 provider endpoints** from small-and-fast to reasonably capable.

The problem is that stacking them by hand is painful: twenty-nine different SDKs, twenty-nine different rate limits, twenty-nine places a request can fail. FreeLLMAPI collapses that into one OpenAI-compatible endpoint. Point any OpenAI client library at your local server, and it routes transparently across whichever providers you'