#!/usr/bin/env python
"""Keep Meta's hosted MCP servers working with the `mcp` Python SDK Hermes ships.

Why this exists
---------------
mcp 2.0.0's `send_raw_request` always writes a `_meta` key into the JSON-RPC params:

    out_params["_meta"] = out_meta     # {} when there is no progress token

Meta's hosted MCP servers (https://mcp.facebook.com/ads and friends) reject that empty
object with HTTP 400 / JSON-RPC -32602:

    "meta" for Request must be an dict or null.

Every request (initialize, tools/list, tools/call) fails, so the server looks unreachable.
Sending no `_meta` at all is accepted, hence this patch:

    if out_meta:
        out_params["_meta"] = out_meta

A non-empty `_meta` (e.g. a progressToken) is written exactly as before, so no other server
is affected.

Why it must run on EVERY host, repeatedly
-----------------------------------------
The patched file lives in site-packages, which is per-machine and outside HERMES_HOME on a
server install (/usr/local/lib/hermes-agent/venv). A Hermes update can restore the unfixed
file. So: run it on each host, and leave it on a timer (every 6h is plenty). It is a no-op
when everything is already patched.

Usage
-----
    python patch_mcp_empty_meta.py            # apply (idempotent)
    python patch_mcp_empty_meta.py --check    # report only
    python patch_mcp_empty_meta.py --root /usr/local/lib/hermes-agent
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ORIGINAL = 'out_params["_meta"] = out_meta'


def default_home() -> Path:
    """HERMES_HOME if set, else %LOCALAPPDATA%/hermes on Windows, else ~/.hermes."""
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    local = os.environ.get("LOCALAPPDATA")
    if local and (Path(local) / "hermes" / "hermes-agent").is_dir():
        return Path(local) / "hermes"
    return Path.home() / ".hermes"


def search_roots(home: Path) -> list[Path]:
    """Every root an mcp install can hide under on this host.

    - HERMES_HOME: the desktop layout keeps venvs, a uv package cache and per-install
      environments underneath it (more than one copy is normal - patch them all, the MCP
      client does not necessarily load the one in hermes-agent/venv).
    - sys.prefix: whichever venv is running this script.
    - /usr/local/lib/hermes-agent: a Linux/server install keeps the venv outside HERMES_HOME,
      so a script that only globs ~/.hermes reports "nothing to do" while the gateway keeps
      failing. (See skills/devops/hermes-multimachine-sync.)
    """
    roots = [home]
    for extra in (Path(sys.prefix), Path("/usr/local/lib/hermes-agent")):
        if extra.is_dir() and extra not in roots:
            roots.append(extra)
    return roots


def targets(home: Path) -> list[Path]:
    """Find every mcp/shared/jsonrpc_dispatcher.py any Hermes on this host could import."""
    patterns = ("**/site-packages/mcp/shared/jsonrpc_dispatcher.py",
                "**/mcp/shared/jsonrpc_dispatcher.py")
    found: list[Path] = []
    for root in search_roots(home):
        for pattern in patterns:
            try:
                found.extend(p for p in root.glob(pattern) if p.is_file())
            except OSError:
                continue
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
                f'{indent}    out_params["_meta"] = out_meta\n'
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
    parser.add_argument("--root", type=Path, default=None, help="extra root to scan (repeatable-ish: pass the venv/install dir)")
    parser.add_argument("--home", type=Path, default=None, help="Hermes home (default: auto-detected)")
    args = parser.parse_args()

    home = args.home or default_home()
    if args.root and args.root.is_dir():
        # allow an explicit extra root by scanning it directly
        files = targets(home)
        files.extend(p for p in args.root.glob("**/mcp/shared/jsonrpc_dispatcher.py") if p.is_file())
        dedup, seen = [], set()
        for f in files:
            k = str(f).lower()
            if k not in seen:
                seen.add(k)
                dedup.append(f)
        files = sorted(dedup)
    else:
        files = targets(home)

    if not files:
        print(f"no mcp/shared/jsonrpc_dispatcher.py found under {home} or {sys.prefix}")
        return 1

    needs = 0
    for path in files:
        state = apply(path, check=args.check)
        needs += state == "needs-patch"
        print(f"[{state}] {path}")

    if args.check:
        print("\nre-run without --check to apply" if needs else "\nall copies already patched")
    else:
        print("\ndone - restart Hermes (and the gateway) so the patched module is imported fresh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
