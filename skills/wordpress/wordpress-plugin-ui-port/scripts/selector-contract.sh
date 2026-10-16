#!/usr/bin/env bash
# Template<->JS data-attribute contract gate for a plugin UI port.
# Usage: selector-contract.sh <data-prefix> <js-file> [dirs-with-templates ...]
# Example: selector-contract.sh data-smc assets/js/smc.js templates includes
#
# Exit 0 = every selector the JS references is emitted by server markup
# (selectors the JS creates dynamically will also match — eyeball the list).
# Exit 1 = missing list printed; those handlers point at markup that no longer exists.
set -euo pipefail

prefix="${1:?data prefix, e.g. data-smc}"
js="${2:?path to the JS file}"
shift 2

[ -f "$js" ] || { echo "JS file not found: $js" >&2; exit 2; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

grep -o "${prefix}-[a-z-]*" "$js" | sort -u > "$tmp/js_sel.txt"
grep -roh "${prefix}-[a-z-]*" "$@" | sort -u > "$tmp/tpl_sel.txt"

missing=$(comm -23 "$tmp/js_sel.txt" "$tmp/tpl_sel.txt" || true)

if [ -n "$missing" ]; then
  echo "MISSING selectors (JS expects, templates never emit):"
  echo "$missing"
  exit 1
fi

echo "OK: every ${prefix}-* selector used by JS exists in the templates."
