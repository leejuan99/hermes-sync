---
name: hermes-multimachine-sync
description: "Sync two Hermes installs; avoid split-brain gateways."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, sync, git, vps, gateway, multi-machine, mcp]
    related_skills: [vps-server-management, hermes-messaging-gateway, hermes-mcp-server-setup]
---

# Syncing Hermes across two machines

Keeping a desktop Hermes and a 24/7 host Hermes on the same content, with git as the transport.

## When to Use

- The user has (or is setting up) more than one Hermes install and they must not drift apart.
- The remote bot cannot reach a skill, memory, or MCP server that works on the desktop.
- Moving Hermes to a 24/7 host, or splitting runtime from config surface.
- A scheduled sync job reports success but the content never arrives.
- Before telling the user "it's synced" — prove it (see Verify).

## The model: one runtime, one config surface

- Exactly one host is the **runtime** — it runs the gateway and the bots (systemd **user** unit plus
  `loginctl enable-linger`, or a logon-independent service). The other machine is the **config
  surface**, where you edit skills and memories. Both roles can live on either machine; only the
  split matters.
- "Identical" means the *content* is identical, not that every file matches. Two hosts with the same
  skills and memories but different `config.yaml` are correct. Two hosts with divergent skills are
  split-brain.
- **Never let both hosts poll the same platform token.** Two gateways on one Telegram bot token
  produce `Conflict: terminated by other getUpdates request` and messages vanish unpredictably.
  Disable the platform on the non-runtime host
  (`hermes config set platforms.telegram.enabled false`) and restart that app so it takes effect.

## Content vs machine-local

Sync — content, identical everywhere:
`skills/`, `memories/`, `plugins/`, `marketing/`, `prompts/`, `SOUL.md`, plus the **extracted**
config fragments `mcp_servers.yaml` and `mcp-tokens/`.

Never sync — machine-local: `config.yaml` (model/provider routing and ports differ per host),
`.env` (tokens, allowlists), `node/`, `cache/`, `logs/`, `cron/`, `installs/`, `sessions/`,
`*.db`, `*.lock`.

**The trap that actually bites:** `mcp_servers` lives *inside* `config.yaml`. Excluding
`config.yaml` wholesale to protect the model section silently ships an install with **zero MCP
servers** — the remote bot then reports the MCP tools are unavailable while the desktop works fine.
Extract that one key to its own tracked file (`hermes config get mcp_servers > mcp_servers.yaml`)
and make the receiving host inject it into its own `config.yaml` on every sync.

## MCP across two hosts

Three things have to travel, and only two of them are files you can commit:

1. **The config** — `mcp_servers.yaml`, injected into the receiving host's `config.yaml`, followed by
   a gateway restart so the tools reload.
2. **The OAuth state** — `mcp-tokens/`. Copying it authorizes the second host with no browser. But
   Hermes **deletes those tokens on start** when the target's `oauth.client_secret` disagrees with
   `client_secret` in `<name>.client.json`; the log blames the client_id, which looks unchanged, so
   align the two secrets before restarting or the host re-auth-loops forever.
3. **Any site-packages patch a server needs** — this lives in the venv, which is per-machine, and
   must be re-applied on each host. Make it self-healing: an idempotent script that greps for the
   unpatched line and rewrites it, on a `0 */6 * * *` cron, survives package updates unnoticed.
   On a Linux/server install that venv sits **outside** `HERMES_HOME`
   (`/usr/local/lib/hermes-agent/venv`), so a patch that only globs `~/.hermes` reports "nothing to
   do" while the gateway keeps failing. Glob `sys.prefix` and `/usr/local/lib/hermes-agent` too.

Symptom that means you missed this: the desktop's MCP tools work, the remote's do not, and the
remote's `hermes mcp list` shows no servers or an empty tool set.

## The model is not where you set it

`hermes config set model.default X` sets the default for **new** sessions only. Three other layers
out-pin it, and a bot that ignores your change is sitting on one of them:

| Layer | Stored in | Rewritten by |
|---|---|---|
| Per-session model | `state.db` (SQLite) → `sessions.model` | every model pick |
| Per-session override | `sessions.json` → `<session>.model_override` | the platform's `/model` command |
| Per-job pin | `cron/jobs.json` → `model_snapshot` | at job creation |

Editing `sessions.json` alone changes nothing — `state.db` is what the gateway reads back. Clear all
three, restart, then re-read `state.db`: if the model reverted, the user is switching it live from
the chat `/model` menu and that write wins over yours. Full recipe: `references/model-routing.md`.

**A chat platform's `/model` menu can break a bot that was working.** The menu lists Hermes' *built-in*
providers, and the free tiers fail (`HTTP 500`, `400 Model is unavailable`) while silently overwriting
the operator's setting. When a bot errors right after it was fine, read the session's model out of
`state.db` before investigating anything else.

**A headless host cannot run a desktop-only provider.** A provider defined in the desktop's
`config.yaml` / `.env` (custom `base_url` + `<X>_API_KEY`) is not "unreadable" on the runtime host —
it was never transferred, because those two files are machine-local by design. Confirm with
`hermes config get providers` (empty means built-ins only) and say plainly that the provider was never
installed there, instead of hunting a parsing bug.

**Drop stale proxy overrides before blaming the network.** If `model.base_url` points at a local proxy
that is down, every call fails at the provider layer:

```bash
hermes config unset model.base_url
hermes config unset model.api_key
```

That hands control back to the provider's real endpoint and the key in `.env`.

## Diagnosing the runtime host

- **Never `grep -r` across `~/.hermes`.** It holds multi-megabyte caches
  (`models_dev_cache.json`, `cache/openrouter_model_metadata.json`) and a live SQLite `state.db` plus
  WAL, so a recursive search both hangs and lies: a model id that merely appears in a catalogue dump
  gets read as a configured setting. Name the file you suspect, or query `state.db` with SQL.
- A setting lives in exactly four places — `config.yaml`, `sessions/sessions.json`,
  `cron/jobs.json`, `state.db`. Search those, not the tree.
- Tool schemas can dominate the request. A host with a large MCP server carries ~150k tokens of
deferred tool schemas (`tool_search activated (tier 1): N deferred (~X tokens)`), which shows up as
double-digit-second latencies and slow cold starts. Check that line before blaming the model.

## Repo shape

A private GitHub repo, one branch. Portal-based `hermes sync` requires a Portal login; the git
transport below needs only a token.

Default-deny `.gitignore`, then allow the content:

```gitignore
*
!.gitignore
!SOUL.md
!skills/**
!memories/**
!plugins/**
!marketing/**
!prompts/**
!mcp_servers.yaml
!mcp-tokens/**
```

`git rm -r --cached .` is refused when a submodule exists anywhere in the tree — use
`git rm -r --cached -f .`. It only touches the index; files on disk stay put.

## Procedure

**Runtime host**, every 5 minutes via cron:

1. `git fetch && git reset --hard origin/main` — the repo is truth for content.
2. `rsync -a --update LIVE/ repo/` — **`--update`, never `--delete`**. Content authored on the
   runtime must be unioned in; `--delete` silently deletes the other host's new skills.
3. Commit and push if anything changed.
4. Inject `mcp_servers` and restart the gateway when it changed.

**Config surface**, every 30 minutes via Scheduled Task / cron: commit local edits,
`git pull --rebase --autostash`, push; retry three times.

When restarting a systemd **user** unit over SSH as root, export `XDG_RUNTIME_DIR=/run/user/0`
first — otherwise `systemctl --user` cannot find the bus and the restart silently does nothing.

## Git pitfalls

- `fatal: expected flush after ref listing` on fetch or push → `git config http.version HTTP/1.1`
  on **both** hosts.
- `fatal: Unable to create '.git/index.lock': File exists` after a crashed git — delete locks older
  than ~5 minutes at the top of the push script. A stale lock makes every scheduled run fail
  silently while the job still reports success.
- Non-fast-forward rejections are normal with two writers; the pull-rebase-push retry is the fix, not
  a longer interval.

## Session state does not move

WhatsApp (Baileys) credentials are device-bound: copying `whatsapp/session/` to another host and
starting there yields `Logged out`, and it breaks the pairing on the original. Re-pair with the QR
flow on whichever host is the runtime. Assume the same for any per-device OAuth session.

## Reporting to this user

Lead with the result, then at most one table. Do **not** restate the same findings once in prose and
again in a status table — this user reads that as "double" (repetitive) and calls it wasteful
("boros"), and has asked for it to stop. Skip the recap section entirely when the answer is one line.

Long answers also cost real money once the runtime host runs a paid model, so brevity is a budget
rule here, not just a style one. When you change the model, state the per-million token price and the
one-line revert command in the same breath.

## Verify

- Push a uniquely-named throwaway file and confirm it appears on the other host after one tick.
  "The repo exists and cron is installed" is not proof — the round-trip is. Delete the file after.
- `git log -1` on both hosts shows the same commit.
- The **live** install, not just the clone, carries the content: count files under
  `~/.hermes/skills/`.
- The receiving host's `config.yaml` really has the servers: `hermes mcp list`.
- Exactly one host has each platform enabled.
