# Cross-machine Hermes sync (desktop ↔ VPS)

Depth for SKILL.md → "Cross-machine Hermes sync (PC ↔ VPS via GitHub)".

## Shape: content duplicated, execution single

| Layer | Scope | How |
|---|---|---|
| Content — `skills/`, `memories/`, `plugins/`, `marketing/`, `prompts/`, `SOUL.md` | identical everywhere | two-way git sync |
| Harness — `config.yaml`, `.env` | per-machine | never synced |
| Runtime — gateway platform adapters, cron scheduler | **one machine** | enabled on the active host only |

The split is forced by the messaging platforms, not by preference: a bot token identifies a *session*, and a second poller on the same token gets `Conflict: terminated by other getUpdates request` and steals updates from the first. Duplicating a bot is not redundancy — the two copies maim each other.

## Choosing and switching the active host

Pick the host that stays up (a VPS beats a desktop that sleeps). Keep the standby's config complete so a switch is a flip, not a rebuild:

```bash
# on the host going ACTIVE
hermes config set platforms.telegram.enabled true
hermes config set platforms.whatsapp.enabled true
systemctl --user restart hermes-gateway        # or restart the desktop app

# on the host going STANDBY
hermes config set platforms.telegram.enabled false
hermes config set platforms.whatsapp.enabled false
```

`platforms.<name>.enabled` in `config.yaml` is the switch. The same names may also exist in `.env`, where a **duplicate key silently wins with its last occurrence** — audit before trusting a value:

```bash
grep -n 'WHATSAPP_ENABLED\|TELEGRAM_ENABLED' ~/.hermes/.env
```

Never leave a list-type allowlist at `*`. `WHATSAPP_ALLOWED_USERS=*` means *any* account can drive the agent; before enabling an adapter on a host, re-check that its allowlist names real accounts.

## Messenger sessions do not migrate by copying files

Copying a Baileys session directory to another host does **not** re-link the account. The bridge starts, reads `creds.json`, and reports:

```
❌ Logged out. Delete session and restart to re-authenticate.
```

while the gateway logs `Reconnect <platform> failed, next retry in 60s` indefinitely. The session material is bound to the enrolling device; a file copy is not a transfer.

To actually move a WhatsApp account: pair it fresh on the target host with `hermes whatsapp` (QR — the user scans from the phone holding the account). Until then, leave the adapter enabled on the host that already holds a working session and disabled on the other; a half-migrated adapter retries forever and floods the logs. Copying the session is still worth doing as a **backup** — just not as a migration.

## Cron: verify the scheduler is the thing doing the work

Enumerate every place a job can live, then read the newest artifact it would have produced:

```bash
crontab -l
systemctl is-active cron          # a brand-new crontab entry proves nothing on its own
ls -lt /root/backups/ | head
sqlite3 -header -column /www/server/panel/data/default.db 'SELECT id,name,type,where1,status FROM crontab;'
journalctl --user -u hermes-gateway --no-pager -n 50    # in-process scheduler
grep 'Gateway running with' ~/.hermes/logs/agent.log | tail -1
```

`*/5` means the next tick is up to 5 minutes away, so "not yet" is normal — distinguish it from "the interval elapsed and nothing happened". The cron daemon being stopped looks identical to a job that never ran.

For the Hermes in-process scheduler, the job list is `cron/jobs.json` and the paused flag is spelled `enabled` (`enabled: false` = paused). The gateway log line `Gateway running with N platform(s)` names how many adapters actually came up; a platform that failed appears separately as `Starting reconnection watcher for N failed platform(s)`.

## Two-way edits and conflict handling

The runner's ordering (capture *before* apply) means a live-side edit is re-read into the repo before the repo is written back, so it survives. Not handled: both sides changing the same file inside one interval — that resolves last-writer-wins. Keeping the interval short is the mitigation; if that is not enough, move the shared fact into a skill (rarely edited) or resolve by hand.

## Reconciling two divergent sets on first sync

The first sync of two machines that have been apart will hit genuine differences: skills present on only one side, and files present on both with different contents.

1. List each side: `comm -23 <(ls A) <(ls B)` (A-only) and `comm -13` (B-only).
2. **Union the unique names** into the repo before applying anything — a skill the runtime actually uses (the `skill:` of a cron job) exists only on the runtime host until you copy it in, and `rsync --delete` on the next tick would otherwise remove it.
3. Back up the live dirs first: `cp -a <live> /root/sync-backup-$(date +%F-%H%M%S)/`.
4. For overlapping files that differ, pick one side deliberately and say which; do not let the first writer win by accident.

Afterwards, confirm anything a scheduled job depends on is still present, and check the **job list** rather than only the filesystem.
