#!/bin/bash
# Clear Hermes session overrides for Telegram
set -e
HERMES_DIR=/root/.hermes
SESSIONS_JSON="$HERMES_DIR/sessions/sessions.json"
STATE_DB="$HERMES_DIR/state.db"

# Remove model_override from sessions.json
if [ -f "$SESSIONS_JSON" ]; then
    cp "$SESSIONS_JSON" "$SESSIONS_JSON.bak"
    # Delete all model_override objects
    python3 - <<'PY'
import json, sys
with open(sys.argv[1], 'r') as f:
    data = json.load(f)
if isinstance(data, dict):
    for key, val in list(data.items()):
        if isinstance(val, dict) and 'model_override' in val:
            del val['model_override']
with open(sys.argv[1], 'w') as f:
    json.dump(data, f, indent=2)
PY "$SESSIONS_JSON"
fi

# Update model and model_config in state.db for telegram sessions
sqlite3 "$STATE_DB" <<'SQL'
UPDATE sessions SET model = 'gemini-3.5-flash', model_config = json('{"gateway_runtime":{"provider":"google","base_url":"https://generativelanguage.googleapis.com/v1beta/openai","api_mode":"chat_completions","fallback_active":false},"model":"gemini-3.5-flash","provider":"google"}') WHERE source = 'telegram';
SQL

echo "Session overrides cleared."
