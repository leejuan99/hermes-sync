#!/usr/bin/env bash
# Probe a remote MCP endpoint BEFORE configuring it in Hermes.
# Answers three questions: is it alive, does it want OAuth (with what scopes), and what
# does its OAuth discovery chain advertise (including whether DCR is offered)?
#
# Usage: probe_mcp_endpoint.sh https://mcp.example.com/ads
set -uo pipefail

URL="${1:?usage: probe_mcp_endpoint.sh <mcp-url>}"
BASE="$(printf '%s' "$URL" | sed -E 's#^(https?://[^/]+).*#\1#')"
SUFFIX="$(printf '%s' "$URL" | sed -E 's#^https?://[^/]+##')"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

printf '\n== 1. initialize (no credentials) -> %s\n' "$URL"
curl -s -o "$WORK/body" -D "$WORK/hdrs" -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  -w 'HTTP %{http_code}\n'
head -c 600 "$WORK/body"
printf '\n'

CHALLENGE="$(grep -i '^www-authenticate:' "$WORK/hdrs" | head -1 | tr -d '\r')"
if [ -z "$CHALLENGE" ]; then
  printf '\nNo auth challenge: the endpoint answered without credentials.\n'
  exit 0
fi

printf '\n== 2. challenge\n%s\n' "$CHALLENGE"

RES_META="$(printf '%s' "$CHALLENGE" | sed -n 's/.*resource_metadata="\([^"]*\)".*/\1/p')"
if [ -n "$RES_META" ]; then
  printf '\n== 3. protected-resource metadata: %s\n' "$RES_META"
  curl -s "$RES_META"
  printf '\n'
fi

# The AS-metadata path is provider-specific: some put it under the resource host with
# the resource path appended, some under the bare host, some under the resource URL.
for cand in \
    "$BASE/.well-known/oauth-authorization-server$SUFFIX" \
    "$BASE/.well-known/oauth-authorization-server" \
    "$URL/.well-known/oauth-authorization-server"
do
  CODE="$(curl -s -o "$WORK/as" -w '%{http_code}' "$cand")"
  if [ "$CODE" = "200" ]; then
    printf '\n== 4. authorization-server metadata: %s\n' "$cand"
    cat "$WORK/as"
    printf '\n'
    break
  fi
done

printf '\nReminder: a registration_endpoint here does NOT guarantee the provider accepts\n'
printf 'Hermes as a dynamic client - see references/oauth-provider-quirks.md.\n'
