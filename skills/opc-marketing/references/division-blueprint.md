# Division blueprint: profiles, agents, board

A concrete, working shape for one division. Copy it per division and swap the roster; the structure
is what transfers. Verified end-to-end on a Linux runtime host.

## The four layers

| Layer | What it is | Cardinality |
|---|---|---|
| Profile | The division: home, memory, skills, sessions, cron | one per division |
| Bot | The division's chat surface (platform connection) | one per division that reports |
| Agent | A cron job with a schedule and a prompt | many — one per recurring duty |
| Sub-agent | `delegate_task` from inside a chat turn | zero — on demand only |

A division with no bot has nowhere to send anything. Before building eight agents, build the bot —
or the agents will run correctly and report into the void.

## Roster (digital marketing, single-product business)

| Agent | Schedule | Duty |
|---|---|---|
| `trend-scout` | `0 7 * * *` | Research today's trends and keywords |
| `content-planner` | `0 8 * * 1` | Build the 7-day calendar as board cards |
| `content-writer` | `0 9 * * *` | Draft captions and scripts |
| `visual-brief` | `0 10 * * *` | Write image/video generation prompts |
| `ads-monitor` | `*/30 9-18 * * *` | Watch paid-ads metrics, flag anomalies |
| `seo-watch` | `0 8 * * 2,4` | Site health, keyword ideas, article pitches |
| `community-manager` | `*/30 8-20 * * 1-6` | Draft replies to comments and DMs |
| `report-daily` | `0 20 * * *` | Progress summary read off the board |

Stagger the schedules. Two long jobs firing on the same minute contend for the same model slot and
produce interleaved logs that are painful to attribute.

## Board flow

`Ide → Draft → Approval → Produksi → Siap Post → Posted → Analisis`

| Column | Moved by | Action |
|---|---|---|
| `Ide` | planner / seo-watch | create the card |
| `Draft` | content-writer | write caption + script |
| `Approval` | content-writer | request the owner's sign-off |
| `Produksi` | visual-brief | attach the visual prompt |
| `Siap Post` | **the human** | approve |
| `Posted` | **the human** | publish |
| `Analisis` | report-daily | record the result |

The two human-owned columns are deliberate. An agent that has no publishing integration must never
be instructed to move a card to `Posted` — it will do so anyway and the board becomes a lie.

## Honesty rules for metrics-bearing agents

Any agent that reports numbers (ads, analytics, community) will invent them when its API is not
connected, because a plausible number is the path of least resistance. Put the prohibition in the
prompt in absolute terms **and hand the agent a literal fallback string to emit instead**:

```
DILARANG menulis angka estimasi / contoh / karangan. Tidak ada pengecualian.
Kalau tidak ada data, output PERSIS:
⚠️ Belum ada akses <API>. Nggak ada angka yang bisa dilaporkan.
```

Without a literal fallback the model emits invented figures the owner cannot distinguish from real
ones. This is the highest-risk failure mode in a marketing division — treat the fallback string as
mandatory, not decorative.

## Prompt delivery

One `.txt` prompt per agent, in a per-division folder:
`~/.hermes/marketing/prompts/<division>/<NN>-<name>.txt`

plus a wrapper that prints it, in the owning profile's scripts directory:

```python
with open('<abs path to prompt>.txt', 'r', encoding='utf-8') as f:
    print(f.read())
```

Generating these over SSH with a here-doc loop mangles `$` expansion and writes wrong paths. Write
the generator locally, `scp` it, run it on the host, and have it self-test every wrapper.

## Verify after building — in this order

1. `hermes -p <profile> skills list | grep <skill>` — the skill is visible to the profile.
2. `python3 <scripts-dir>/<wrapper>.py` for every wrapper — each prints its prompt.
3. `grep 'tick .* profile(s) under multiplex' ~/.hermes/logs/gateway.log` — the gateway serves the profile.
4. `hermes -p <profile> cron run <job>` — then read `errors.log`, not just the status line.

Step 4 is where provider-level problems surface. Steps 1–3 passing while step 4 fails means the
plumbing is right and the model call is not.
