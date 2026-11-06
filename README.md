# My AI Boilerplate

This repository is a library of Claude Code skills, configurations, and orchestration setups that developers can study, copy, and install into their own projects. It is not a runnable application — it is a learning resource and a toolkit. Browse it to understand how to teach Claude Code your team's rules, then copy the parts you need.

---

## Learning path

Work through these guides in order for your first hour with Claude Code.

1. [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) — Install Claude Code, start a session, and try your first skill end to end.
2. [docs/CONCEPTS.md](docs/CONCEPTS.md) — Understand CLAUDE.md, skills, subagents, hooks, and orchestration so you know what each folder does.
3. [docs/SKILLS-CATALOG.md](docs/SKILLS-CATALOG.md) — Browse every skill in this repo, see which ones are generic and which are project-specific examples.

---

## Repo map

| Directory | What is in it |
|-----------|---------------|
| `coding-skills/` | Skills for writing, reviewing, planning, explaining, and orchestrating code — the largest collection in the repo |
| `review-work/` | Skills for code critique, bug review, and security review |
| `study-and-documentation/` | Skills for learning, explaining code to beginners, and generating documentation |
| `configurations/` | Reusable CLAUDE.md / AGENTS.md templates and project-specific coding rules you can copy to your own project |
| `orchestration/` | An installable master / worker / sonar agent package with hooks; copy `orchestration/core/` into any project |

---

## Heads up

**Some skills are project-specific examples.** Skills such as `local-setup`, `api-endpoint`, `product-thinking-plan`, and `staging-release` were written for specific codebases. They are included so you can read them as templates, not to run them directly. The catalog marks each one clearly.

**Two spec workflow families exist — start with speckit.** The `.claude/skills/speckit*` family (in the untracked local skills directory) is the current standard spec-driven development workflow; start there with `speckit-init`. The `coding-skills/spec-driven-*` family is a legacy version being retired; it still works but new projects should use speckit.

**`main.py` and `.codex/config.toml` are a minimal MCP server demo.** MCP (Model Context Protocol) is a standard that lets Claude connect to external tools. `main.py` defines a small demo server using FastMCP with one tool (`add`), one resource (`get_greeting`, at `greeting://{name}`), and one prompt (`greet_user`). `.codex/config.toml` points a Codex client to the local server URL. Neither file is part of the skill system; they demonstrate what an MCP server looks like.
