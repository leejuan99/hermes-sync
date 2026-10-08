#!/usr/bin/env python
"""Regenerate the synced `mcp_servers.yaml` fragment WITHOUT redacted secrets.

Why not `hermes config get mcp_servers`
--------------------------------------
That command redacts secret values before printing:

    $ hermes config get mcp_servers
    ...
    WP_API_PASSWORD: BtFh...yojG      <-- 11 chars, a placeholder
    client_secret:    fc0d...730a     <-- 11 chars, a placeholder

So the documented recipe (`hermes config get mcp_servers > mcp_servers.yaml`) writes placeholders
into the file that is synced to the other host. Two consequences:

1. The receiving host injects bogus credentials into its `config.yaml` -> its MCP servers fail to
authenticate.
2. OAuth servers specifically: Hermes deletes cached tokens on start when `oauth.client_secret`
disagrees with `client_secret` in `mcp-tokens/<name>.client.json`. The placeholder is exactly that
disagreement, and the log blames the client_id (which looks unchanged), so the host re-auth-loops.

This script reads `config.yaml` as a FILE (no redaction) and writes the fragment with real values.

Usage
-----
    python write_mcp_fragment.py            # regenerate (timestamped backup first)
    python write_mcp_fragment.py --check    # report mismatches only, write nothing
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

SECRET_ISH = ("secret", "password", "token", "api_key", "apikey")


def default_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    local = os.environ.get("LOCALAPPDATA")
    if local and (Path(local) / "hermes" / "hermes-agent").is_dir():
        return Path(local) / "hermes"
    return Path.home() / ".hermes"


def walk_secrets(node, path=""):
    """Yield (dotted_path, value) for every secret-looking scalar."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            if isinstance(value, str) and any(s in str(key).lower() for s in SECRET_ISH):
                yield here, value
            else:
                yield from walk_secrets(value, here)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from walk_secrets(item, f"{path}[{i}]")


def describe(value: str) -> str:
    digest = hashlib.sha256(value.encode()).hexdigest()[:10]
    return (f"len={len(value):<3} sha={digest} "
            f"placeholder={'YES' if '...' in value else 'no'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report only, do not write")
    parser.add_argument("--home", type=Path, default=default_home())
    args = parser.parse_args()

    config_path = args.home / "config.yaml"
    frag_path = args.home / "mcp_servers.yaml"
    if not config_path.exists():
        print(f"config.yaml not found at {config_path}")
        return 1

    live = (yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}).get("mcp_servers") or {}
    if not live:
        print("config.yaml has no mcp_servers key")
        return 1

    old = {}
    if frag_path.exists():
        old = (yaml.safe_load(frag_path.read_text(encoding="utf-8")) or {}).get("mcp_servers") or {}

    old_secrets = dict(walk_secrets(old))
    new_secrets = dict(walk_secrets(live))

    bad = [k for k, v in old_secrets.items() if new_secrets.get(k) != v]
    print(f"servers in config.yaml     : {len(live)}")
    print(f"servers in mcp_servers.yaml: {len(old)}")
    print(f"\nsecret fields compared: {len(new_secrets)}")
    for key in sorted(new_secrets):
        before = old_secrets.get(key)
        same = before == new_secrets[key]
        print(f"  [{'OK ' if same else 'MISMATCH'}] {key}")
        print(f"            fragment: {describe(before) if before is not None else '(absent)'}")
        if not same:
            print(f"            config  : {describe(new_secrets[key])}")

    if bad:
        print(f"\n{len(bad)} secret field(s) differ or are missing in the fragment.")
    else:
        print("\nFragment already matches config.yaml.")

    if args.check:
        print("\n--check: nothing written.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if frag_path.exists():
        backup = frag_path.with_suffix(f".yaml.bak-{stamp}")
        shutil.copy2(frag_path, backup)
        print(f"\nbackup written: {backup}")

    payload = yaml.safe_dump(
        {"mcp_servers": live}, sort_keys=False, allow_unicode=True,
        default_flow_style=False, width=100
    )
    frag_path.write_text(payload, encoding="utf-8")
    print(f"wrote {frag_path} ({len(live)} servers, real secrets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
