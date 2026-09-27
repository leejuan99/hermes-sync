#!/usr/bin/env python3
"""
Novamira Sandbox Pollution Cleanup Script

This script connects to a Novamira MCP server and cleans up sandbox pollution
by removing/disabling test PHP files that auto-load and pollute the JSON-RPC stream.

Usage:
    python novamira_sandbox_cleanup.py --url <mcp_url> --username <user> --password <pass>
    python novamira_sandbox_cleanup.py --config ~/.hermes/config.yaml --profile default

Requires: novamira MCP server configured in Hermes
"""

import json
import sys
import argparse
import subprocess
import os
from pathlib import Path

def run_mcp_command(command, args):
    """Run an MCP command via hermes CLI"""
    env = os.environ.copy()
    env.update({
        "WP_API_URL": args.url,
        "WP_API_USERNAME": args.username,
        "WP_API_PASSWORD": args.password,
    })
    
    cmd = [
        "hermes", "chat", "-q",
        f"Use the Novamira MCP server to {command}",
        "--toolsets", "mcp"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    return result.returncode == 0, result.stdout, result.stderr

def list_sandbox_files():
    """List all PHP files in the sandbox"""
    # This would be called via MCP
    pass

def disable_test_files():
    """Disable all test_*.php files in sandbox"""
    # This would be called via MCP
    pass

def main():
    parser = argparse.ArgumentParser(description="Clean up Novamira sandbox pollution")
    parser.add_argument("--url", help="Novamira MCP URL (e.g., https://site.com/wp-json/mcp/novamira)")
    parser.add_argument("--username", help="WordPress username")
    parser.add_argument("--password", help="Application password")
    parser.add_argument("--config", help="Path to Hermes config.yaml")
    parser.add_argument("--profile", help="Hermes profile name")
    parser.add_argument("--dry-run", action="store_true", help="List files without modifying")
    
    args = parser.parse_args()
    
    if args.config:
        # Load from Hermes config
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)
        # Extract MCP server config...
        pass
    
    if not args.url or not args.username or not args.password:
        parser.error("Must provide --url, --username, --password or --config")
    
    print(f"Connecting to Novamira at {args.url}...")
    
    # List sandbox files
    success, stdout, stderr = run_mcp_command(
        "list all PHP files in wp-content/novamira-sandbox/ directory",
        args
    )
    
    if not success:
        print(f"Failed to list sandbox: {stderr}")
        return 1
    
    print("Sandbox files:")
    print(stdout)
    
    if args.dry_run:
        return 0
    
    # Create bootstrap cleanup file
    print("Creating 00_bootstrap_cleanup.php...")
    success, stdout, stderr = run_mcp_command(
        "write file 00_bootstrap_cleanup.php that disables test_write.php",
        args
    )
    
    if success:
        print("Bootstrap cleanup created. Test MCP connection now.")
    else:
        print(f"Failed: {stderr}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())