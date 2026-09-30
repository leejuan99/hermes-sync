# Moving a Hermes gateway or cron job off a pinned model

`hermes config set model.default X` only changes the default for **new** sessions. Existing sessions
and jobs hold their own pin and keep using the old model until you clear it everywhere below.

Back up first: `state.db`, `sessions/sessions.json`, `cron/jobs.json`.

## 1. Read the pinned models (SQL, never grep)

```bash
python3 - <<'PY'
import sqlite3
c = sqlite3.connect('/root/.hermes/state.db')
for r in c.execute("SELECT id, source, session_key, model FROM sessions "
                   "WHERE archived=0 ORDER BY last_activity_at DESC LIMIT 10"):
    print(r)
PY
```

`sessions.model` is what the gateway reads back on the next turn. `billing_provider` and
`billing_base_url` sit beside it and reveal which provider the pin resolves to.

## 2. Clear all three layers

**a. Session model** — one UPDATE per platform worth changing:

```sql
UPDATE sessions SET model='deepseek/deepseek-v3.2', billing_provider='openrouter'
WHERE source IN ('telegram','whatsapp');
```

**b. `sessions.json` override** — it nests inside `metadata`, so a top-level `del` misses it:

```bash
python3 - <<'PY'
import json
p='/root/.hermes/sessions/sessions.json'
d=json.load(open(p)); n=0
def scrub(o):
    global n
    if isinstance(o, dict):
        if o.pop('model_override', None): n+=1
        for v in o.values(): scrub(v)
    elif isinstance(o, list):
        for v in o: scrub(v)
scrub(d)
json.dump(d, open(p,'w'), indent=2, ensure_ascii=False)
print('removed', n)
PY
```

**c. Cron jobs** — `cron/jobs.json` carries a `model_snapshot` per job. Rewrite it (or delete the key)
for **every** job, otherwise the scheduled work keeps running on the old model while the bot looks
fixed. Verify with `hermes cron list` if available, else re-read the JSON.

## 3. Apply

```bash
export XDG_RUNTIME_DIR=/run/user/0
systemctl --user restart hermes-gateway
```

Without that export the `--user` restart silently does nothing when run as root over SSH.

## 4. Confirm it stuck

Re-read `state.db`. If `sessions.model` is back to the old value, the user is switching the model live
from the chat `/model` menu — that write beats yours and no amount of config editing will hold. Fix
the habit (and say so), not the config.

## 5. Cost

Moving off a `*-free` tier onto a paid model is a real cost change. Quote the per-million input/output
price and give the one-line revert (`hermes config set model.default <old>`) in the same report.
