#!/usr/bin/env python3
"""
Fetch all Fluent CRM contacts via Novamira MCP server.

Usage:
    python fetch-all-contacts.py --output contacts.json --per-page 100
    python fetch-all-contacts.py --output contacts.json --wp-url https://site.com/wp-json/mcp/novamira --wp-user user --wp-pass pass
"""

import json
import subprocess
import argparse
import os
import sys
from typing import List, Dict

def fetch_page(wp_url: str, wp_user: str, wp_pass: str, per_page: int, page: int) -> Dict:
    """Fetch a single page of contacts via MCP."""
    
    # Build the JSON-RPC request
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "fetch-contacts", "version": "1.0.0"}
        }
    }
    
    call_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "mcp-adapter-execute-ability",
            "arguments": {
                "ability_name": "fluent-crm/list-contacts",
                "parameters": {
                    "per_page": per_page,
                    "page": page
                }
            }
        }
    }
    
    # Prepare input
    input_data = json.dumps(init_msg) + "\n" + json.dumps(call_msg) + "\n"
    
    # Environment
    env = os.environ.copy()
    env.update({
        "WP_API_URL": wp_url,
        "WP_API_USERNAME": wp_user,
        "WP_API_PASSWORD": wp_pass,
    })
    
    # Run npx
    try:
        result = subprocess.run(
            ["npx", "-y", "@automattic/mcp-wordpress-remote@latest"],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
    except subprocess.TimeoutExpired:
        raise Exception(f"Timeout fetching page {page}")
    except FileNotFoundError:
        # Try Windows path
        result = subprocess.run(
            [r"C:\Program Files\nodejs\npx.cmd", "-y", "@automattic/mcp-wordpress-remote@latest"],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
    
    if result.returncode != 0:
        raise Exception(f"npx failed (code {result.returncode}): {result.stderr}")
    
    # Parse output - second line is the tools/call response
    lines = result.stdout.strip().split('\n')
    if len(lines) < 2:
        raise Exception(f"Unexpected output format: {result.stdout[:200]}")
    
    try:
        response = json.loads(lines[1])
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response: {e}\nOutput: {result.stdout[:500]}")
    
    if 'error' in response:
        raise Exception(f"MCP error: {response['error']}")
    
    # Extract the double-encoded JSON
    text_content = response['result']['content'][0]['text']
    data = json.loads(text_content)
    
    if not data.get('success'):
        raise Exception(f"Ability failed: {data}")
    
    return data['data']

def main():
    parser = argparse.ArgumentParser(description='Fetch all Fluent CRM contacts via Novamira MCP')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--wp-url', required=True, help='WordPress MCP endpoint URL')
    parser.add_argument('--wp-user', required=True, help='WordPress username')
    parser.add_argument('--wp-pass', required=True, help='WordPress application password')
    parser.add_argument('--per-page', type=int, default=100, help='Contacts per page (max 100)')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to fetch (default: all)')
    args = parser.parse_args()
    
    print(f"Fetching contacts from {args.wp_url}")
    print(f"Per page: {args.per_page}")
    
    all_contacts = []
    page = 1
    total_pages = None
    
    while True:
        if args.max_pages and page > args.max_pages:
            print(f"Reached max pages limit ({args.max_pages})")
            break
        
        print(f"Fetching page {page}...", end=" ", flush=True)
        
        try:
            data = fetch_page(args.wp_url, args.wp_user, args.wp_pass, args.per_page, page)
        except Exception as e:
            print(f"\nError on page {page}: {e}")
            break
        
        items = data.get('items', [])
        all_contacts.extend(items)
        
        total = data.get('total', 0)
        pages = data.get('pages', 0)
        
        if total_pages is None:
            total_pages = pages
            print(f"Total: {total} contacts, {pages} pages")
        else:
            print(f"Got {len(items)} contacts (total so far: {len(all_contacts)})")
        
        if page >= pages or len(items) == 0:
            print("Done!")
            break
        
        page += 1
    
    # Save
    with open(args.output, 'w') as f:
        json.dump(all_contacts, f, indent=2)
    
    print(f"\nSaved {len(all_contacts)} contacts to {args.output}")
    print(f"Expected total: {total}, Fetched: {len(all_contacts)}")
    
    if len(all_contacts) != total:
        print("WARNING: Count mismatch! Some contacts may be missing.")

if __name__ == '__main__':
    main()