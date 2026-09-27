* [Issues 52](https://github.com/NVIDIA/SkillSpector/issues)
* [Pull requests 45](https://github.com/NVIDIA/SkillSpector/pulls)
* [Discussions](https://github.com/NVIDIA/SkillSpector/discussions)
* Actions
* Projects
* Security and quality
* Insights

...

# Folders and files
## Repository files navigation
* README
* Contributing
* Apache-2.0 license
* Security
More items

...

# SkillSpector
## Overview
SkillSpector is part of the [NVIDIA Verified Skills pipeline](https://docs.nvidia.com/skills/) , which scans, evaluates, and signs agent skills before publication. Skills that pass are published to the [NVIDIA skills catalog](https://github.com/NVIDIA/skills) .

## Documentation
* **[Scan agent skills before installation](https://docs.nvidia.com/skills/scanning-agent-skills)** — Hosted guide: when to scan, how to read a report, and how to gate installs.
* **Development guide** — Architecture, package layout, and how to extend the analyzer pipeline.

...

## Features
* **Multi-format input** : Scan Git repos, URLs, zip files, directories, or single files

...

## Quick Start
### Installation
> **Open-source software notice:** This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.

...

```
#  Clone the repository 
git clone https://github.com/NVIDIA/skillspector.git
 cd skillspector

 #  Create and activate virtual environment 
uv venv .venv && source .venv/bin/activate
 #  or: python3 -m venv .venv && source .venv/bin/activate 

 #  Install for production use 
make install

```

...

### Basic Usage
```
#  Scan a local skill directory 
skillspector scan ./my-skill/

 #  Scan a single SKILL.md file 
skillspector scan ./SKILL.md

 #  Scan a Git repository 
skillspector scan https://github.com/user/my-skill

 #  Scan a zip file 
skillspector scan ./my-skill.zip
```

...

### MCP Server
```
#  Install, or reinstall if you already used the CLI-only path 
uv tool install --force ' skillspector[mcp] @ git+https://github.com/NVIDIA/skillspector.git ' 

 #  FastMCP stdio transport for local CLI agents 
skillspector mcp

 #  streamable HTTP/SSE transport for remote / A2A callers 
```

...

## Integrating SkillSpector
### Machine-readable output
`--format json` produces a JSON report; with no `--output` / `-o` it is written to stdout:
```
skillspector scan ./my-skill/ --format json
```
The top-level shape is (this example shows a full LLM-backed scan; with `--no-llm` , `metadata.llm_requested` is `false` ):

...

## Development
### Setup
```
#  Clone, create venv, activate, install dev dependencies 
git clone https://github.com/NVIDIA/skillspector.git
 cd skillspector
uv venv .venv && source .venv/bin/activate
 #  or: python3 -m venv .venv && source .venv/bin/activate 
make install-dev

 #  Run tests 
make test 

 #  Run tests with coverage 
make test-cov

```

...

## About
Security scanner for AI agent skills. Detect vulnerabilities, malicious patterns, security risks, prompt injection, data exfiltration, and supply-chain risks in Claude Code, Codex, and MCP skills before you install them.
[docs.nvidia.com/skills/scanning-agent-skills](https://docs.nvidia.com/skills/scanning-agent-skills)

...

### Forks
**1.2k** forks
[Report repository](https://github.com/contact/report-content?content_url=https%3A%2F%2Fgithub.com%2FNVIDIA%2FSkillSpector&report=NVIDIA+%28user%29)