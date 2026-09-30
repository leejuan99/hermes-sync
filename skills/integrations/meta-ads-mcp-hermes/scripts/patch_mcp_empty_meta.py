#!/usr/bin/env python
"""Re-apply the Meta Ads MCP compatibility patch after a Hermes update.

Why this exists
---------------
Hermes talks to remote MCP servers through the `mcp` Python SDK. mcp 2.0.0's
`send_raw_request` always writes a `_meta` key into the JSON-RPC params:

    out_params["_meta"] = out_meta     # {} when there is no progress token

Meta's hosted MCP servers (https://mcp.facebook.com/ads and friends) reject that
empty object with HTTP 400 / JSON-RPC -32602:

    "meta" for Request must be an dict or null.

Every request (initialize, tools/list, tools/call) fails, so the server looks
unreachable. Sending no `_meta` at all is accepted, hence this patch:

    if out_meta:
        out_params["_meta"] = out_meta

It is safe for other servers: a non-empty `_meta` (e.g. a progressToken) is still
written exactly as before.

Usage
-----
    python patch_mcp_empty_meta.py           # apply (idempotent)
    python patch_mcp_empty_meta.py --check   # report only

Run it after `hermes update` if the Meta Ads (or any Meta-hosted) MCP server
starts failing with "HTTP 400 from POST https://mcp.facebook.com/ads" again.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _default_home() -> Path:
    """HERMES_HOME if set, else %LOCALAPPDATA%/hermes on Windows, else ~/.hermes."""
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    local = os.environ.get("LOCALAPPDATA")
    if local and (Path(local) / "hermes" / "hermes-agent").is_dir():
        return Path(local) / "hermes"
    return Path.home() / ".hermes"


HERMES_HOME = _default_home()
ORIGINAL = 'out_params["_meta"] = out_meta'


def targets(root: Path) -> list[Path]:
    """Every `mcp/shared/jsonrpc_dispatcher.py` Hermes may import mcp from.

    A Windows install carries at least three: hermes-agent/venv,
    installs/<id>/environments/<id>/venv, and the uv package cache. The one the
    MCP client actually loads is not necessarily hermes-agent/venv.
    """
    found: list[Path] = []
    found.extend(p for p in root.glob("**/site-packages/mcp/shared/jsonrpc_dispatcher.py") if p.is_file())
    for extra in (root / "cache",):
        if extra.is_dir():
            found.extend(p for p in extra.glob("**/mcp/shared/jsonrpc_dispatcher.py") if p.is_file())
    seen, unique = set(), []
    for path in found:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return sorted(unique)


def inspect(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "if out_meta:" in text and 'out_params["_meta"] = out_meta' in text:
        return "patched"
    if ORIGINAL in text:
        return "needs-patch"
    return "unrecognised"


def apply(path: Path, *, check: bool) -> str:
    state = inspect(path)
    if state != "needs-patch" or check:
        return state
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out_lines, hits = [], 0
    for line in lines:
        if line.strip() == ORIGINAL:
            indent = line[: len(line) - len(line.lstrip())]
            out_lines.append(
                f"{indent}if out_meta:\n"
                f"{indent}    # Only emit `_meta` when it carries something: Meta's hosted MCP\n"
                f"{indent}    # servers reject an empty `_meta` object with -32602.\n"
                f"{indent}    out_params[\"_meta\"] = out_meta\n"
            )
            hits += 1
        else:
            out_lines.append(line)
    if hits != 1:
        return f"skipped (found {hits} candidate lines)"
    shutil.copy2(path, path.with_suffix(".py.bak-empty-meta"))
    path.write_text("".join(out_lines), encoding="utf-8")
    return "patched"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report state without writing")
    parser.add_argument("--home", type=Path, default=HERMES_HOME, help="Hermes home (default: auto-detected)")
    args = parser.parse_args()

    files = targets(args.home)
    if not files:
        print(f"No mcp/shared/jsonrpc_dispatcher.py found under {args.home}")
        return 1

    needs = 0
    for path in files:
        state = apply(path, check=args.check)
        needs += state == "needs-patch"
        print(f"[{state}] {path}")

    if args.check:
        print("\nRe-run without --check to apply." if needs else "\nAll copies already patched.")
    else:
        print("\nDone. Restart Hermes (and the gateway) so the patched module is imported fresh.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
