#!/usr/bin/env bash
# Test Composio connection via Hermes terminal

set -euo pipefail

if [[ -z "${COMPOSIO_API_KEY:-}" ]]; then
  echo "Error: COMPOSIO_API_KEY not set"
  echo "Export it first: export COMPOSIO_API_KEY='your_key'"
  exit 1
fi

ENTITY_ID="wp_user_1"  # adjust if needed

# List connected accounts
print_blue() { echo -e "\033[0;34m$*\033[0m"; }
print_green() { echo -e "\033[0;32m$*\033[0m"; }
print_red() { echo -e "\033[0;31m$*\033[0m"; }

print_blue "=== Connected Accounts ==="
curl -s -H "Authorization: Bearer $COMPOSIO_API_KEY" \
     https://backend.composio.dev/api/v3/connected_accounts | \
     jq -r '.items[] | "\(.toolkit.slug): \(.status)"' | sort

# Test a simple tool (Facebook get_authenticated_user)
print_blue "\n=== Test Facebook get_authenticated_user ==="
RESPONSE=$(curl -s -H "Authorization: Bearer $COMPOSIO_API_KEY" \
               -H "Content-Type: application/json" \
               -d '{"entity_id":"'$ENTITY_ID'","toolkit_slug":"facebook","tool_name":"get_authenticated_user","args":{}}' \
               https://backend.composio.dev/api/v3/tools/execute)

if echo "$RESPONSE" | grep -q '"success":true'; then
  print_green "SUCCESS: Facebook token valid"
  echo "$RESPONSE" | jq '.result'
else
  print_red "FAILED: "
  echo "$RESPONSE" | jq '.error.message // .'
fi
