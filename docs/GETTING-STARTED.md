# Your first hour with Claude Code

This guide takes you from zero to running your first skill. No prior Claude Code experience needed.

---

## Step 1 — Install Claude Code

Claude Code is a command-line AI coding assistant made by Anthropic.

The common install method is:

```
npm install -g @anthropic-ai/claude-code
```

See the official docs for the current recommended method and any platform-specific steps:
https://docs.claude.com/en/docs/claude-code/overview

You need Node.js 18 or later and a Claude subscription (Pro, Max, Team or Enterprise) or an Anthropic API key.

---

## Step 2 — Start a session

A **session** is a single Claude Code conversation that runs in your terminal. To start one:

1. Open a terminal.
2. Change to any project directory (or this repo's root).
3. Run:

```
claude
```

Claude Code reads any `CLAUDE.md` file it finds in the current directory and parent directories. It uses that file to load project rules and context before you type anything.

---

## Step 3 — Ask for things and approve tool use

Type a plain English request at the prompt. For example:

```
Explain what the main.py file does.
```

Claude may ask permission before it reads files or runs commands. This is the **tool use approval** step — a safety check. Read what Claude proposes to do, then type `y` to allow it or `n` to decline. You can also set auto-approval for specific actions in a `settings.json` file inside your project's `.claude/` directory once you are comfortable. See `orchestration/core/.claude/settings.json` in this repo for a working example.

There is no special command syntax required. You ask in plain English and Claude responds.

---

## Step 4 — Try your first skill end to end

A **skill** is a folder that contains a `SKILL.md` file. The SKILL.md tells Claude exactly how to perform a specific task. Installing a skill copies that folder so Claude can find it.

We will use `briefly-explain` from this repo. It has no project-specific dependencies — it just explains selected code in beginner-friendly terms.

### Install the skill

For all your projects (global install), copy the skill folder to `~/.claude/skills/`:

```
cp -r /path/to/My-AI-Boilerplate/study-and-documentation/briefly-explain ~/.claude/skills/briefly-explain
```

For one project only, copy it to that project's `.claude/skills/` directory:

```
cp -r /path/to/My-AI-Boilerplate/study-and-documentation/briefly-explain .claude/skills/briefly-explain
```

### Invoke the skill

Start a Claude Code session in your project, then either:

- Ask naturally: `"Briefly explain the auth module for me."`
- Or type the skill name as a slash command: `/briefly-explain`

### What success looks like

Claude will return a short, plain-English explanation of the code you selected or described. It will cover purpose, logic, and syntax — aimed at someone new to the codebase. If you see that explanation, the skill is working correctly.

---

## Glossary

| Term | What it means |
|------|---------------|
| **session** | A single Claude Code conversation started by running `claude` in a terminal. It ends when you close the terminal or type `/exit`. |
| **CLAUDE.md** | A file Claude reads automatically at session start. It loads project rules, context, and agent routing instructions into every conversation in that directory. |
| **skill** | A folder with a `SKILL.md` file that teaches Claude a reusable behavior or workflow. Install by copying the folder; invoke with `/skill-name` or plain language. |
| **subagent** | A named AI role defined in `.claude/agents/<name>.md`. Claude delegates specific work (planning, implementing, reviewing) to the right subagent automatically based on instructions in `CLAUDE.md`. |
| **hook** | A shell script that Claude runs automatically at defined points — session start, session end, or before/after specific tool calls. Configured in a `settings.json` file inside your project's `.claude/` directory. |
| **MCP** | Model Context Protocol. A standard that lets Claude connect to external tools and data sources via a small server. The `main.py` in this repo is a demo MCP server. |

---

## Safe habits

- **Review diffs before accepting.** Claude will show you what it plans to change. Read it before typing `y`.
- **Commit before big changes.** If Claude is about to make large edits, commit your current work first so you can roll back easily.
- **Never paste secrets.** Do not paste API keys, passwords, or tokens into the Claude Code prompt. They may appear in logs.
- **Start with read-only tasks.** Ask Claude to explain or review before you ask it to change anything. This builds trust in what it does.
- **Check the skill's project scope.** Some skills in this repo were written for specific projects. Read the SKILL.md before installing to confirm it fits your codebase.
