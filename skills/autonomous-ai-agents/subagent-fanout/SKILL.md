---
name: subagent-fanout
description: "Use when fanning out parallel subagents for audits/fixes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
tags: [delegation, subagents, parallel, audit, code-review]
metadata:
  hermes:
    tags: [delegation, subagents, parallel, audit, code-review]
    related_skills: [code-review, diagnosing-bugs]
---

# Parallel Subagent Fan-out

## When to Use

Large work that splits into INDEPENDENT modules — codebase audit, multi-module bug fix, parallel review/research. The user asks for this as "panggil pasukan". Do NOT use for sequential dependent steps, small tasks, or anything needing mid-task user input.

## Solo vs fan-out (explain this when the user asks)

- Fan-out costs roughly 2x the tokens of solo (each child carries its own context; summaries return to the parent), but finishes ~N times faster on divisible work and keeps the orchestrator context clean for synthesis.
- Solo wins for small, sequential, or interactive work.
- Check real numbers anytime: `C:\Users\pc\AppData\Local\hermes\state.db` → table `session_model_usage`: `SELECT session_id, task, SUM(input_tokens), SUM(output_tokens) FROM session_model_usage GROUP BY session_id, task`. Main chat = task `(main)`; each child gets its own session_id. Cost columns read 0 for custom/unbilled providers.

## Procedure

1. Material first: get the target source local (scp/clone). VERIFY the on-disk layout before dispatch — `scp -r host:/path/dir local/` nests the folder (`local/dir/dir/`). Flatten: `cp -r dir/. . && rm -rf dir` so every path handed to children is correct from their first call.
2. Split by module with EXCLUSIVE file ownership per task. Two tasks that would edit the same file must be merged into one, or run in separate waves (e.g. wave 1 backend fixes, wave 2 UI redesign). Parallel editors on one file always conflict.
3. Task context must be self-contained (children know nothing of the conversation): exact file list, host access (SSH command + paths), acceptance criteria, the bug classes or rubric to apply, and an output_schema (findings: severity/file/title/issue/impact/fix). Include "report only what you actually see in the code — do not invent issues".
4. Children mostly self-correct path errors via search_files; watch live transcripts under `C:\Users\pc\AppData\Local\hermes\cache\delegation\live\<deleg_id>\` and use delegate_task(action='steer') only if one is genuinely stuck.
5. Results are SELF-REPORTS: dedupe findings across modules (the same root bug gets reported from two angles), and independently verify any external side effect (upload, deploy, remote write) before telling the user it happened.
6. For production FIX agents, embed the verification protocol in the context: backup (tar to a backups dir) → scp fresh copy of each file → patch → scp back → syntax check (php -l / node --check) → smoke test (site HTTP 200 + boot probe like `wp eval 'echo "boot-ok";'`). Never leave it implied.

## Pitfalls

- scp -r nested-directory surprise breaks every child's first reads at once — flatten and re-verify paths BEFORE dispatching.
- Do not move/rename the source tree while children run; they cache discovered absolute paths and their next reads fail.
- Cross-module duplicates inflate counts — dedupe before reporting totals to the user.
- A child editing production without the backup/verify protocol is how live sites break — make the protocol mandatory in the task context, not a suggestion.
