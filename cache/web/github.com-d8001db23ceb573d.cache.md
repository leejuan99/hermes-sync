# mattpocock/skills
URL: https://github.com/mattpocock/skills.git

# mattpocock/skills

Skills for Real Engineers. Straight from my .agents directory.

- Stars: 217296
- Forks: 18718
- Watchers: 217296
- Open issues: 338
- License: MIT License
- Homepage: https://aihero.dev/skills
- Default branch: main
- Created: 2026-02-03T11:15:53Z

## Languages

- JavaScript
- Shell

## Top Contributors

- mattpocock (407 contributions)
- TESTPERSONAL (8 contributions)
- github-actions[bot] (6 contributions)
- claude (4 contributions)

---

## README

 
 
 
 
 
 
 
 
 

# Skills For Real Engineers

[![skills.sh](https://skills.sh/b/mattpocock/skills)](https://skills.sh/mattpocock/skills)

My agent skills that I use every day to do real engineering - not vibe coding.

Developing real applications is hard. Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process. But while doing so, they take away your control and make bugs in the process hard to resolve.

These skills are designed to be small, easy to adapt, and composable. They work with any model. They're based on decades of engineering experience. Hack around with them. Make them your own. Enjoy.

If you want to keep up with changes to these skills, and any new ones I create, you can join ~60,000 other devs on my newsletter:

[Sign Up To The Newsletter](https://www.aihero.dev/s/skills-newsletter)

## Installation (30-second setup)

Two ways in, two philosophies. **The [Claude Code plugin](https://code.claude.com/docs/en/plugins)** installs the whole set as a managed, read-only bundle that updates when I ship â you subscribe rather than fork. **[skills.sh](https://skills.sh/mattpocock/skills)** copies editable skill files into your project, so you can hack on them and make them your own. Pick one â installing both leaves you with every skill twice.

### 1. Get the skills

 
 Claude Code 

```bash
claude plugins install mattpocock-skills
```

Or, from inside a session:

```
/plugin install mattpocock-skills
```

It's in Claude Code's official marketplace, so there's nothing to add first, and updates arrive automatically.

 

 
 Codex, and other agents 

```bash
npx skills@latest add mattpocock/skills
```

Pick the skills you want, and which coding agents to install them on. **The installer lets you choose which skills to take â make sure `setup-matt-pocock-skills` is one of them.**

A native Codex plugin is on the roadmap â see [`.agents/adr/0002-ship-as-a-claude-code-plugin.md`](./.agents/adr/0002-ship-as-a-claude-code-plugin.md).

 

 
 For tinkerers 

Use the same installer, on any agent â including Claude Code:

```bash
npx skills@latest add mattpocock/skills
```

It writes the skills into your repo as ordinary files you own and can edit. Nothing updates behind your back; pull my latest changes when you want them with `npx skills update`.

 

### 2. Run `/setup-matt-pocock-skills`

In your agent, run it once per repo. It will:

- Ask you which issue tracker you want to use (GitHub, Linear, or local files)
- Ask you what labels you apply to tickets when y