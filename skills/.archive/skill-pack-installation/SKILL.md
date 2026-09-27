---
name: skill-pack-installation
description: Install third-party skill packs for AI coding agents.
category: autonomous-ai-agents
---

# Skill Pack Installation

This skill covers the process of installing third‑party skill packs (collections of slash‑command skills) for AI coding agents such as Claude Code, Codex, OpenCode, Cursor, Hermes, etc. It includes steps for cloning the repository, running the provided setup script, linking the skill pack to the agent’s configuration, and handling platform‑specific quirks.

## When to Use

- You want to add a new skill pack like **gstack**, **custom‑agent‑skills**, or any community‑provided skill collection.
- You need to update an existing skill pack to the latest version.
- You encounter errors during installation (e.g., non‑empty target directory, missing dependencies).

## Prerequisites

- Git installed and available in `PATH`.
- For most modern skill packs: **Bun** (`bun --version`) **or** Node.js (`node --version`) and npm/yarn/pnpm.
- Access to the agent’s configuration directory (e.g., `~/.claude/skills/` for Claude Code, `~/.codex/skills/` for Codex, etc.).
- Basic shell proficiency (bash/zsh/PowerShell). On Windows, use Git Bash or WSL for best compatibility.

## Standard Installation Procedure

1. **Choose the target agent**  
   Determine which agent you are installing for. Common locations:
   - Claude Code: `~/.claude/skills/`
   - OpenCode: `~/.config/opencode/skills/`
   - Codex: `~/.codex/skills/`
   - Cursor: `~/.cursor/skills/`
   - Hermes: `~/.hermes/skills/` (or the active profile’s skills folder)
   - Adjust paths if you use a custom profile or environment.

2. **Clone the repository**  
   Use a shallow, single‑branch clone to keep the download small:
   ```bash
   git clone --single-branch --depth 1 <REPO_URL> <TARGET_DIR>/<SKILL_PACK_NAME>
   ```
   Example for gstack:
   ```bash
   git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
   ```

3. **Run the setup script**  
   Most skill packs ship a `setup` script at the repository root. Make it executable and run it:
   ```bash
   cd <TARGET_DIR>/<SKILL_PACK_NAME>
   chmod +x ./setup   # if needed on *nix
   ./setup
   ```
   Some packs accept flags (e.g., `--host <agent>`) to install for a specific agent. Consult the pack’s README.

4. **Link the skill pack in the agent’s config**  
   Many agents read a `CLAUDE.md` (or similar) file in the project root to discover skills. Add a section that lists the newly installed skill(s).
   Example for Claude Code:
   ```markdown
   ## gstack
   Use /browse from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.
   Available skills: /office-hours, /plan-ceo-review, /plan-eng-review, ... (see pack’s README)
   ```
   If the agent automatically discovers skills from the `skills/` directory, this step may be unnecessary.

5. **Verify installation**  
   Restart the agent session (or reload its configuration) and try a signature command from the pack, e.g. `/office-hours` for gstack. If the agent responds with the skill’s usage, installation succeeded.

## Common Pitfalls & Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `fatal: destination path '...' already exists and is not an empty directory` | The target folder exists from a previous attempt and contains files (often a `.git` folder). | Remove the directory first: `rm -rf <TARGET_DIR>/<SKILL_PACK_NAME>` then retry the clone. On Windows using Git Bash, ensure you have permission; alternatively, use a different folder name. |
| `command not found: bun` | Bun is not installed or not in PATH. | Install Bun from https://bun.sh/ or fallback to Node.js: many packs also accept `./setup --host <agent>` that works with Node. Install Node.js (≥18) and npm, then run `npm install` if the script expects it. |
| `Permission denied` when running `./setup` | The script lacks execute permission. | Run `chmod +x ./setup` before executing, or invoke explicitly: `bash ./setup`. |
| Agent does not recognize new skills | The agent’s skill directory is not being scanned, or the `CLAUDE.md` section is missing. | Verify the agent reads from the correct `skills/` folder (check its documentation). Add or correct the reference in the project’s `CLAUDE.md`. Restart the agent/IDE to reload configurations. |
| Setup script fails with missing dependencies (e.g., `playwright` install errors) | System lacks required build tools or browser dependencies. | Install system dependencies: on Windows, ensure you have the C++ build tools via `vs_buildtools.exe`; on Linux, install `libgconf-2-4`, `libnss3`, etc., or follow the pack’s prerequisites guide. |
| After installation, commands give “command not found” or “skill not loaded” | The skill pack’s `SKILL.md` files are not properly formatted or the agent’s skill cache is stale. | Delete the agent’s skill cache (often a `.cache` folder inside the skills directory) and restart. For Claude Code, delete `~/.claude/scache/` or similar. |

## Updating an Installed Skill Pack

To pull the latest changes:
```bash
cd <TARGET_DIR>/<SKILL_PACK_NAME>
git pull   # or `git fetch && git reset --hard origin/main` if you have local changes
./setup   # re‑run the setup script to pick up new scripts or config changes
```
If you previously used `--host <agent>` during the initial install, repeat the same flag with `./setup`.

## Windows‑Specific Notes

- Use **Git Bash** (installed with Git for Windows) or **WSL** for a Unix‑like shell; the native Windows Command Prompt or PowerShell may mis‑handle POSIX paths and `./setup` syntax.
- Bun may have issues with Playwright’s pipe transport on Windows; if the pack’s `browse`‑related skills fail, the setup script often falls back to Node.js automatically. Ensure both `bun` and `node` are on your PATH.
- Symbolic links (`ln -snf`) may not work correctly outside Developer Mode; the setup script will fall back to copying files. Re‑run `./setup` after each `git pull` to refresh any copied files.

## Verification Checklist

After installation, run through this quick checklist:

- [ ] The skill pack’s folder exists under the agent’s `skills/` directory.
- [ ] The `setup` script ran without errors.
- [ ] At least one signature command from the pack responds (e.g., `/office-hours` for gstack).
- [ ] The agent’s help or skill list shows the new commands.
- [ ] No stray files remain in `/tmp` or the home directory from the installation process.

## Advanced: Installing Multiple Agent Targets

Some skill packs support simultaneous installation for several agents via host flags:
```bash
./setup --host claude --host codex --host opencode
```
Consult the pack’s `README` or `docs/ADDING_A_HOST.md` for the exact syntax and supported host names.

## Removing a Skill Pack

To completely remove a skill pack:
```bash
rm -rf <TARGET_DIR>/<SKILL_PACK_NAME>
```
Then, remove any references you added to the project’s `CLAUDE.md` (or equivalent) and restart the agent.

---
*This skill is intended to be reused across sessions. Keep it updated as you encounter new skill packs or platform‑specific quirks.*