---
name: jev-decisions
description: "Use when a task needs a fast typed decision, not prose."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [decisions, classification, routing, typesafe, openrouter, system-one]
---

# Jev Decisions (TypeSafe via OpenRouter)

Jev is a **System One decision model**, not a chat LLM. Send a `state` (facts)
plus typed `questions`, get back **typed answers with probabilities** — no prose,
no reasoning trace. Use it when code must branch on a crisp answer: routing,
classification, guardrail/gate checks, grading against a rubric. Output tokens
are free; you pay input tokens only (cheap: ~$0.00002/call for small states).

**It is NOT a Hermes agent model.** Hermes provider `api_mode` only supports
chat surfaces (`chat_completions`, `responses`, `anthropic_messages`). Jev
returns no text, so it can never be `model.default`. Call it as a **tool**:
from the terminal, a cron job, a skill, or a hook.

## Endpoints

| Surface | Endpoint | When |
|---|---|---|
| Decisions API | `POST https://openrouter.ai/api/alpha/decisions` | plain HTTP / OpenRouter SDKs |
| System One API | `POST https://openrouter.ai/api/v1/systemone` | official TypeSafe SDK, just change `base_url` to `https://openrouter.ai/api` |

- **Model ID:** `typesafe/jev-1.13` (alias `~typesafe/jev-latest`).
- **Auth:** your normal OpenRouter key (`$OPENROUTER_API_KEY`). No separate
  TypeSafe account or waitlist.
- **Context:** 32K tokens (`state` + `questions`).
- Chat-completions SDKs will **NOT** work — different request/response shape.

## Primitives (the three question types)

| type | question | returns |
|---|---|---|
| `noul` | yes/no | `noul`: P(yes) in `0..1` |
| `choice` | pick one of N | `choice` (winning key), `probabilities` per option, `confidence` |
| `score` | position on ordered rubric | `score` (weighted position), `probabilities` per level, `confidence`, `legend` |

`noul` ~0.5 = coin flip (not "medium"). `score` index 0 = first criterion you
listed. `confidence` describes how concentrated the option distribution is —
**not** whether the workflow is safe to run; pick thresholds from the cost of
each kind of mistake.

## Usage

```bash
cd ~/AppData/Local/hermes && set -a && . ./.env && set +a   # loads OPENROUTER_API_KEY
python skills/integrations/jev-decisions/scripts/jev.py \
  --state '{"message":"Mas, filter nya kok bunyi terus?"}' \
  --questions-file q.json --pretty --answers-only
```

On the VPS (Linux): `cd ~/.hermes && set -a && . ./.env && set +a`, same
command with that path.

`scripts/jev.py` takes `--state`/`--state-file` and `--questions`/
`--questions-file`, plus `--model`, `--session-id`, `--pretty`,
`--answers-only`. It is stdlib-only (urllib), no `requests` dependency.

Minimal questions file (`q.json`):

```json
{
  "is_support": { "type": "noul",
    "instructions": "Is this a product support question?",
    "criteria": {"true":"Asks about operation/maintenance.","false":"Billing or unrelated."} },
  "intent": { "type": "choice",
    "instructions": "What does the customer want?",
    "criteria": {"troubleshoot":"Wants help.","buy":"Wants to purchase.","complaint":"Unhappy/refund."} },
  "urgency": { "type": "score",
    "instructions": "How urgent?",
    "criteria": ["Can wait, informational","Should respond today","Blocking use of product"] }
}
```

Response shape:

```json
{
  "answers": {
    "is_support": {"type":"noul","noul":0.98},
    "intent": {"type":"choice","choice":"troubleshoot","probabilities":{"troubleshoot":1,"buy":0,"complaint":0},"confidence":1.0},
    "urgency": {"type":"score","score":0.89,"probabilities":{"0":0.16,"1":0.79,"2":0.05},"confidence":0.69,"legend":{"0":"...","1":"...","2":"..."}}
  },
  "usage": {"input_tokens":480,"output_tokens":77,"cost":0.00002016},
  "id": "gen-dec-...", "model": "typesafe/jev-1.13-20260917", "provider": "TypeSafe"
}
```

The response `model` field names a dated snapshot — expected when you send the
unpinned `typesafe/jev-1.13`. Pin the dated ID if thresholds must stay stable
across releases.

## Pitfalls

- **Don't try to set it as the Hermes model.** It has no text output; the agent
  loop needs a chat model. Use it as a tool call.
- **Don't use chat SDKs / `/v1/chat/completions`.** Use the Decisions endpoint.
- **Questions in one request can't see each other's answers.** They run in
  parallel; put only *independent* questions together. Chain dependent ones in
  separate requests (or combine with deterministic code).
- **No explanation comes back.** If you need a written justification, make the
  decision with Jev then have a chat model explain it (or route low-confidence
  cases to a human).
- **Pick thresholds from mistake cost**, not from a round number like 0.9.
- On Windows the env-load line is `set -a && . ./.env && set +a` in bash
  (git-bash); the key lives in `.env` as `OPENROUTER_API_KEY`.
- **`scripts/` in the hermes home is NOT synced** to the VPS (only `skills/`,
  `memories/`, `plugins/`, `SOUL.md`, `marketing/` are tracked by `hermes-sync`).
  Keep helper scripts inside the skill dir, never in the home `scripts/`.

## Cost

Input tokens only; output free. Every response carries `usage.cost` in USD.

## References

- Model page: https://openrouter.ai/typesafe/jev-1.13
- Docs hub: https://openrouter.ai/docs/guides/community/jev
- Tutorial: https://openrouter.ai/docs/guides/community/jev-tutorial
- API ref: https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-questions-and-answers-request
- TypeSafe concepts: https://docs.typesafe.ai/concepts/system-one
- Cookbooks (gating, cascades, classification): https://openrouter.ai/docs/guides/community/jev#cookbooks
