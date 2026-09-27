# mattpocock/skills
- Page: GitHub repository
- URL: https://github.com/mattpocock/skills
- Description: Skills for Real Engineers. Straight from my .agents directory. - mattpocock/skills
- Stars: 260,668
- Forks: 21,985
- License: MIT license
- Default branch: main
- Created: 2026-02-03T11:15:53.000Z
- Commits: 459

## Top-level files
- .agents/
- .changeset/
- .claude-plugin/
- .github/workflows/
- .out-of-scope/
- docs/
- scripts/
- skills/
- .gitignore
- AGENTS.md
- CHANGELOG.md
- CLAUDE.md
- CONTEXT.md
- LICENSE
- README.md
- package-lock.json
- package.json

# Skills For Real Engineers
[skills.sh](https://skills.sh/mattpocock/skills)
My agent skills that I use every day to do real engineering - not vibe coding.
Developing real applications is hard. Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process. But while doing so, they take away your control and make bugs in the process hard to resolve.
These skills are designed to be small, easy to adapt, and composable. They work with any model. They're based on decades of engineering experience. Hack around with them. Make them your own. Enjoy.

...

## Installation (30-second setup)
Two ways in, two philosophies. **The [Claude Code plugin](https://code.claude.com/docs/en/plugins)** installs the whole set as a managed, read-only bundle that updates when I ship, so you subscribe rather than fork.
**[skills.sh](https://skills.sh/mattpocock/skills)** copies editable skill files into your project, so you can hack on them and make them your own. Pick one: installing both leaves you with every skill twice.

### 1. Get the skills
**Claude Code**
```shell
claude plugins install mattpocock-skills
```
Or, from inside a session:
```
/plugin install mattpocock-skills
```
It's in Claude Code's official marketplace, so there's nothing to add first, and updates arrive automatically. **Codex, and other agents**
```shell
npx skills@latest add mattpocock/skills
```
Pick the skills you want, and which coding agents to install them on. **The installer lets you choose which skills to take, so make sure `setup-matt-pocock-skills` is one of them.**
A native Codex plugin is on the roadmap (see [`.agents/adr/0002-ship-as-a-claude-code-plugin.md`](https://github.com/mattpocock/skills/blob/main/.agents/adr/0002-ship-as-a-claude-code-plugin.md) ). **For tinkerers**
Use the same installer, on any agent, including Claude Code:
```shell
npx skills@latest add mattpocock/skills
```
It writes the skills into your repo as ordinary files you own and can edit. Nothing updates behind your back; pull my latest changes when you want them with `npx skills update` .

### 2. Run `/setup-matt-pocock-skills`
In your agent, run it once per repo. It will:
* Ask you which issue tracker you want to use (GitHub, Linear, or local files)
* Ask you what labels you apply to tickets when you triage them ( `/triage` uses labels)
* Ask you where you want to save any docs we create

## Why These Skills Exist
I built these skills as a way to fix common failure modes I see with Claude Code, Codex, and other coding agents.

...

### #1: The Agent Didn't Do What I Want
* [`/grill-me`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) - for non-code uses
* [`/grill-with-docs`](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md) - same as [`/grill-me`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) , but adds more goodies (see below)

...

### #2: The Agent Is Way Too Verbose
**The Problem** : At the start of a project, devs and the people they're building the software for (the domain experts) are usually speaking different languages.
I felt the same tension with my agents. Agents are usually dropped into a project and asked to figure out the jargon as they go. So they use 20 words where 1 will do.
**The Fix** for this is a shared language. It's a document that helps agents decode the jargon used in the project.
Example
Here's an example [`CONTEXT.md`](https://github.com/mattpocock/course-video-manager/blob/076a5a7a182db0fe1e62971dd7a68bcadf010f1c/CONTEXT.md) , from my `course-video-manager` repo. Which one is easier to read?

...

This is built into [`/grill-with-docs`](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md) . It's a grilling session, but that helps you build a shared language with the AI, and document hard-to-explain decisions in ADR's.

...

* **Variables, functions and files are named consistently** , using the shared language
* As a result, the **codebase is easier to navigate** for the agent
* The agent also **spends fewer tokens on thinking** , because it has access to a more concise language

...

### #3: The Code Doesn't Work
I've built a **[`/tdd`](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md) skill** you can slot into any project. It encourages red-green-refactor and gives the agent plenty of guidance on what makes good and bad tests.
For debugging, I've also built a **[`/diagnosing-bugs`](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md)** skill that wraps best debugging practices into a disciplined loop, gated phase by phase.

...

### #4: We Built A Ball Of Mud
* [`/to-spec`](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md) quizzes you about which modules you're touching before creating a spec
And crucially, [`/improve-codebase-architecture`](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md) surveys a codebase for deepening opportunities and hands you the candidates. I recommend running it on your codebase once every few days.

...

## Reference
These split on one axis: who can invoke them. **User-invoked** skills are reachable only when you type them (e.g. `/grill-me` ); their job is to orchestrate. **Model-invoked** skills can be invoked by you _or_ reached for automatically by the agent when the task fits; they hold the reusable discipline.
A user-invoked skill may invoke model-invoked skills, but never another user-invoked one.

### Engineering
Skills I use daily for code work.
**User-invoked**
* **[ask-matt](https://github.com/mattpocock/skills/blob/main/skills/engineering/ask-matt/SKILL.md)** : Ask which skill or flow fits your situation. A router over the user-invoked skills in this repo.
* **[grill-with-docs](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md)** : Grilling session that also builds your project's domain model, sharpening terminology and updating `CONTEXT.md` and ADRs inline.
* **[triage](https://github.com/mattpocock/skills/blob/main/skills/engineering/triage/SKILL.md)** : Move issues through a state machine of triage roles.
* **[improve-codebase-architecture](https://github.com/mattpocock/skills/blob/main/skills/engineering/improve-codebase-architecture/SKILL.md)** : Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
* **[setup-matt-pocock-skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md)** : Configure this repo for the engineering skills (issue tracker, triage labels, domain doc layout). Run once per repo before using the other engineering skills.
* **[to-spec](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md)** : Turn the current conversation into a spec and publish it to the issue tracker. No interview, just synthesizes what you've already discussed.
* **[to-tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md)** : Break any plan, spec, or conversation into a set of tracer-bullet tickets, each declaring its blocking edges, written as text in a local file, or as native blocking links on a real tracker.
* **[implement](https://github.com/mattpocock/skills/blob/main/skills/engineering/implement/SKILL.md)** : Build the work described by a spec or set of tickets, driving `/tdd` at pre-agreed seams and closing out with `/code-review` before committing.
* **[wayfinder](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md)** : Plan a huge chunk of work, more than one agent session can hold, as a shared map of decision tickets on the issue tracker, and resolve them one at a time until the way to the destination is clear.
**Model-invoked**
* **[prototype](https://github.com/mattpocock/skills/blob/main/skills/engineering/prototype/SKILL.md)** : Build a throwaway prototype to answer a design question, either a single shareable HTML file for state/logic questions, or several radically different UI variations toggleable from one route.
* **[diagnosing-bugs](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md)** : Disciplined diagnosis loop for hard bugs and performance regressions: build a feedback loop that goes red on this bug → minimise → hypothesise → instrument → fix → regression-test.
* **[research](https://github.com/mattpocock/skills/blob/main/skills/engineering/research/SKILL.md)** : Investigate a question against high-trust primary sources and capture the findings as a cited Markdown file in the repo, run as a background agent.
* **[tdd](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md)** : Test-driven development with a red-green-refactor loop. Builds features or fixes bugs one vertical slice at a time.
* **[domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)** : Actively build and sharpen a project's domain model: challenge terms against the glossary, stress-test with edge-case scenarios, and update `CONTEXT.md` and ADRs inline.
* **[codebase-design](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md)** : Shared discipline and vocabulary for designing deep modules: a lot of behaviour behind a small interface, placed at a clean seam, testable through that interface.
* **[code-review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md)** : Two-axis review of the diff since a fixed point: **Standards** (does it follow the repo's coding standards, plus a Fowler smell baseline?) and **Spec** (does it faithfully implement the originating issue/spec?), run as
parallel sub-agents so neither pollutes the other.
* **[resolving-merge-conflicts](https://github.com/mattpocock/skills/blob/main/skills/engineering/resolving-merge-conflicts/SKILL.md)** : Work through an in-progress git merge or rebase conflict hunk by hunk, resolving by intent traced to each side's primary source, then finish the operation (never `--abort` ).
* **[wizard](https://github.com/mattpocock/skills/blob/main/skills/engineering/wizard/SKILL.md)** : Generate an interactive bash wizard that walks a human through steps only they can perform: provisioning infrastructure, setting up credentials or CI secrets, walking an unfamiliar third-party dashboard, or running a one-off
migration or cutover.

### Productivity
General workflow tools, not code-specific.
**User-invoked**
* **[grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md)** : Get relentlessly interviewed about a plan or design until every branch of the design tree is resolved.
* **[handoff](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md)** : Compact the current conversation into a handoff document so another agent can continue the work.
* **[teach](https://github.com/mattpocock/skills/blob/main/skills/productivity/teach/SKILL.md)** : Teach the user a new skill or concept over multiple sessions, using the current directory as a stateful teaching workspace.
* **[to-questionnaire](https://github.com/mattpocock/skills/blob/main/skills/productivity/to-questionnaire/SKILL.md)** : Turn a decision you can't answer alone into a Markdown questionnaire for the one person who can, filled in async, or together over a meeting.
It grills you about the send (who it's for, what you need back), not the subject.
* **[wait-what](https://github.com/mattpocock/skills/blob/main/skills/productivity/wait-what/SKILL.md)** : Fire this the moment a message doesn't land.
The agent re-pitches it with the context you're missing, in plain English, using your `CONTEXT.md` vocabulary.
**Model-invoked**
* **[grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)** : Interview the user relentlessly about a plan, decision, or idea until every branch of the design tree is resolved.
The reusable interview primitive behind `grill-me` , `grill-with-docs` , `triage` , `wayfinder` and `improve-codebase-architecture` .
* **[writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)** : Writing documents for agents: skills, AGENTS.md/CLAUDE.md, and any doc an agent reaches by a pointer.