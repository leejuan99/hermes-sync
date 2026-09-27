#!/usr/bin/env python3
"""
Agent Reach Platform Health Check Script

Run this to verify which platforms are working and which backend is active.
Equivalent to `agent-reach doctor --json` but with more detail and as a reusable script.
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


def run_cmd(cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
    """Run command and return structured result."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "TIMEOUT", "returncode": -1}
    except FileNotFoundError:
        return {"success": False, "stdout": "", "stderr": "COMMAND_NOT_FOUND", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def check_command_exists(cmd: str) -> bool:
    """Check if command exists in PATH."""
    result = run_cmd(["which", cmd] if sys.platform != "win32" else ["where", cmd])
    return result["success"]


def check_yt_dlp_js_runtime() -> bool:
    """Check if yt-dlp has JS runtime configured."""
    cfg_path = Path.home() / "AppData" / "Roaming" / "yt-dlp" / "config"
    if not cfg_path.exists():
        return False
    content = cfg_path.read_text()
    return "--js-runtimes node" in content


def test_platform(name: str, test_cmd: List[str], success_indicators: List[str] = None) -> Dict[str, Any]:
    """Test a platform with a command."""
    result = run_cmd(test_cmd, timeout=60)
    success = result["success"]
    if success_indicators:
        success = all(indicator in result["stdout"] for indicator in success_indicators)
    return {
        "platform": name,
        "command": " ".join(test_cmd),
        "available": success,
        "output_preview": result["stdout"][:200] if result["stdout"] else result["stderr"][:200],
        "backend": "detected" if success else "failed",
    }


def main():
    print("=" * 60)
    print("Agent Reach Platform Health Check")
    print("=" * 60)
    
    results = {
        "zero_config": [],
        "login_backed": [],
        "optional_enhancements": [],
        "environment": {},
    }
    
    # Environment info
    results["environment"] = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "agent_reach_installed": check_command_exists("agent-reach"),
        "yt_dlp_js_runtime": check_yt_dlp_js_runtime(),
        "gh_cli": check_command_exists("gh"),
        "node": check_command_exists("node"),
        "npm": check_command_exists("npm"),
        "mcporter": check_command_exists("mcporter"),
        "opencli": check_command_exists("opencli"),
        "twitter_cli": check_command_exists("twitter"),
        "bili_cli": check_command_exists("bili"),
        "rdt_cli": check_command_exists("rdt"),
        "xhs_cli": check_command_exists("xhs"),
    }
    
    print(f"\nEnvironment: Python {results['environment']['python']} on {results['environment']['platform']}")
    print(f"  agent-reach: {'✓' if results['environment']['agent_reach_installed'] else '✗'}")
    print(f"  yt-dlp JS runtime: {'✓' if results['environment']['yt_dlp_js_runtime'] else '✗'}")
    print(f"  gh CLI: {'✓' if results['environment']['gh_cli'] else '✗'}")
    print(f"  mcporter: {'✓' if results['environment']['mcporter'] else '✗'}")
    print(f"  opencli: {'✓' if results['environment']['opencli'] else '✗'}")
    print(f"  twitter-cli: {'✓' if results['environment']['twitter_cli'] else '✗'}")
    print(f"  bili-cli: {'✓' if results['environment']['bili_cli'] else '✗'}")
    print(f"  rdt-cli: {'✓' if results['environment']['rdt_cli'] else '✗'}")
    
    # Zero-config platforms
    print("\n" + "-" * 60)
    print("ZERO-CONFIG PLATFORMS")
    print("-" * 60)
    
    # Web (Jina Reader)
    r = test_platform("Web (Jina Reader)", ["curl", "-s", "https://r.jina.ai/https://example.com"], ["Example Domain"])
    results["zero_config"].append(r)
    print(f"  Web: {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    
    # YouTube
    r = test_platform("YouTube (yt-dlp)", ["yt-dlp", "--dump-json", "--no-download", "https://youtube.com/watch?v=dQw4w9WgXcQ"], ["id"])
    results["zero_config"].append(r)
    print(f"  YouTube: {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    
    # GitHub
    r = test_platform("GitHub (gh CLI)", ["gh", "repo", "view", "torvalds/linux", "--json", "name"], ["torvalds"])
    results["zero_config"].append(r)
    print(f"  GitHub: {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    
    # Bilibili (search API)
    r = test_platform("Bilibili (search API)", ["curl", "-s", "https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword=test&page=1"], ["result"])
    results["zero_config"].append(r)
    print(f"  Bilibili (search): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    
    # Bilibili (bili-cli if installed)
    if results["environment"]["bili_cli"]:
        r = test_platform("Bilibili (bili-cli)", ["bili", "search", "test", "--type", "video", "-n", "1"], [])
        results["zero_config"].append(r)
        print(f"  Bilibili (bili-cli): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    
    # V2EX
    r = test_platform("V2EX", ["curl", "-s", "https://www.v2ex.com/api/topics/hot.json", "-H", "User-Agent: agent-reach/1.0"], ["title"])
    results["zero_config"].append(r)
    print(f"  V2EX: {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    
    # RSS
    r = test_platform("RSS (feedparser)", [sys.executable, "-c", "import feedparser; print('ok')"], ["ok"])
    results["zero_config"].append(r)
    print(f"  RSS (feedparser): {'✓' if r['available'] else '✗'}")
    
    # Exa Search
    if results["environment"]["mcporter"]:
        r = test_platform("Exa Search (mcporter)", ["mcporter", "call", "exa.web_search_exa(query: 'test', numResults: 1)"], ["results"])
        results["zero_config"].append(r)
        print(f"  Exa Search: {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    else:
        results["zero_config"].append({
            "platform": "Exa Search (mcporter)",
            "available": False,
            "output_preview": "mcporter not installed"
        })
        print(f"  Exa Search: ✗ - mcporter not installed")
    
    # Login-backed platforms
    print("\n" + "-" * 60)
    print("LOGIN-BACKED PLATFORMS (require setup)")
    print("-" * 60)
    
    # Twitter
    if results["environment"]["twitter_cli"]:
        r = test_platform("Twitter (twitter-cli)", ["twitter", "feed", "-n", "1"], [])
        results["login_backed"].append(r)
        print(f"  Twitter (twitter-cli): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    elif results["environment"]["opencli"]:
        r = test_platform("Twitter (OpenCLI)", ["opencli", "twitter", "feed", "-f", "yaml"], [])
        results["login_backed"].append(r)
        print(f"  Twitter (OpenCLI): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    else:
        results["login_backed"].append({"platform": "Twitter", "available": False, "output_preview": "No backend available"})
        print(f"  Twitter: ✗ - No backend (install twitter-cli or opencli)")
    
    # Reddit
    if results["environment"]["opencli"]:
        r = test_platform("Reddit (OpenCLI)", ["opencli", "reddit", "hot", "-f", "yaml"], [])
        results["login_backed"].append(r)
        print(f"  Reddit (OpenCLI): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    elif results["environment"]["rdt_cli"]:
        r = test_platform("Reddit (rdt-cli)", ["rdt", "popular", "--limit", "1"], [])
        results["login_backed"].append(r)
        print(f"  Reddit (rdt-cli): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    else:
        results["login_backed"].append({"platform": "Reddit", "available": False, "output_preview": "No backend (install opencli or rdt-cli)"})
        print(f"  Reddit: ✗ - No backend")
    
    # XiaoHongShu
    if results["environment"]["opencli"]:
        r = test_platform("XiaoHongShu (OpenCLI)", ["opencli", "xiaohongshu", "feed", "-f", "yaml"], [])
        results["login_backed"].append(r)
        print(f"  XiaoHongShu (OpenCLI): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    else:
        results["login_backed"].append({"platform": "XiaoHongShu", "available": False, "output_preview": "No backend (install opencli)"})
        print(f"  XiaoHongShu: ✗ - No backend")
    
    # Facebook
    if results["environment"]["opencli"]:
        r = test_platform("Facebook (OpenCLI)", ["opencli", "facebook", "feed", "--limit", "1", "-f", "yaml"], [])
        results["login_backed"].append(r)
        print(f"  Facebook (OpenCLI): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    else:
        results["login_backed"].append({"platform": "Facebook", "available": False, "output_preview": "No backend (install opencli)"})
        print(f"  Facebook: ✗ - No backend")
    
    # Instagram
    if results["environment"]["opencli"]:
        r = test_platform("Instagram (OpenCLI)", ["opencli", "instagram", "explore", "--limit", "1", "-f", "yaml"], [])
        results["login_backed"].append(r)
        print(f"  Instagram (OpenCLI): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
    else:
        results["login_backed"].append({"platform": "Instagram", "available": False, "output_preview": "No backend (install opencli)"})
        print(f"  Instagram: ✗ - No backend")
    
    # LinkedIn
    if results["environment"]["mcporter"]:
        # Check if linkedin MCP is configured
        r = run_cmd(["mcporter", "config", "list"])
        has_linkedin = "linkedin" in r["stdout"]
        if has_linkedin:
            r = test_platform("LinkedIn (MCP)", ["mcporter", "call", "linkedin.search_people(query: 'test', limit: 1)"], [])
            results["login_backed"].append(r)
            print(f"  LinkedIn (MCP): {'✓' if r['available'] else '✗'} - {r['output_preview'][:80]}")
        else:
            results["login_backed"].append({"platform": "LinkedIn (MCP)", "available": False, "output_preview": "MCP not configured"})
            print(f"  LinkedIn (MCP): ✗ - MCP not configured")
    else:
        results["login_backed"].append({"platform": "LinkedIn", "available": False, "output_preview": "mcporter not installed"})
        print(f"  LinkedIn: ✗ - mcporter not installed")
    
    # Optional enhancements
    print("\n" + "-" * 60)
    print("OPTIONAL ENHANCEMENTS")
    print("-" * 60)
    
    if results["environment"]["bili_cli"]:
        print(f"  bili-cli: ✓ installed")
        results["optional_enhancements"].append({"tool": "bili-cli", "installed": True})
    else:
        print(f"  bili-cli: ✗ not installed (pipx install bilibili-cli)")
        results["optional_enhancements"].append({"tool": "bili-cli", "installed": False})
    
    if results["environment"]["xhs_cli"]:
        print(f"  xhs-cli: ✓ installed (legacy)")
        results["optional_enhancements"].append({"tool": "xhs-cli", "installed": True})
    else:
        print(f"  xhs-cli: ✗ not installed (legacy, use OpenCLI instead)")
        results["optional_enhancements"].append({"tool": "xhs-cli", "installed": False})
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    zero_ok = sum(1 for r in results["zero_config"] if r["available"])
    zero_total = len(results["zero_config"])
    login_ok = sum(1 for r in results["login_backed"] if r["available"])
    login_total = len(results["login_backed"])
    
    print(f"Zero-config: {zero_ok}/{zero_total} working")
    print(f"Login-backed: {login_ok}/{login_total} working")
    print(f"\nTotal channels active: {zero_ok + login_ok}")
    
    if zero_ok < zero_total:
        print("\n⚠️  Fix zero-config issues first (they're free and easy):")
        for r in results["zero_config"]:
            if not r["available"]:
                print(f"   - {r['platform']}: {r['output_preview'][:100]}")
    
    if login_ok < login_total:
        print("\n🔐 Login-backed platforms need setup:")
        for r in results["login_backed"]:
            if not r["available"]:
                print(f"   - {r['platform']}: {r['output_preview'][:100]}")
    
    # Save JSON for programmatic use
    output_path = Path.home() / ".agent-reach" / "health-check.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\n📄 Full results saved to: {output_path}")
    
    return 0 if zero_ok == zero_total else 1


if __name__ == "__main__":
    sys.exit(main())