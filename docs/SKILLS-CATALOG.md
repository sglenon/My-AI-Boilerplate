# Skills Catalog

This file lists every skill in this repository. Use it to find the right skill, understand what it does, and decide whether it applies to your project.

---

## How to install and use a skill

A skill is a folder that contains a `SKILL.md` file. Install by copying the folder to Claude Code's skills directory:

**All projects (global):**
```
cp -r <skill-folder> ~/.claude/skills/<skill-name>/
```

**One project only:**
```
cp -r <skill-folder> <project>/.claude/skills/<skill-name>/
```

After installing, start a Claude Code session with `claude` in your project directory. Invoke the skill by asking in plain English or by typing `/<skill-name>`.

---

## Spec workflow (speckit) — start here

> **This is the current standard spec-driven development workflow.** Start with `speckit-init` to set up a project, then follow the stage order below. These skills live in `.claude/skills/` (a local skills directory not yet committed to the repo) and will be the definitive family going forward.

| Skill | Purpose | Generic or Project-specific |
|-------|---------|----------------------------|
| `speckit` | Spec-Driven Development (SDD) toolkit — overview, routing table, template resolution stack, and hook lifecycle reference. Run speckit-init to set up a project. See individual speckit-\<command\> skills for each stage. | Generic |
| `speckit-init` | Initialize .specify/ in a project, or register/unregister presets and extensions. Lists available presets and extensions from the global catalog. Writes init-options.json (ai_skills=true, ai=claude) and integration.json for skills-mode hook rendering. Idempotent — never clobbers an existing constitution.md, spec, or already-registered preset/extension. | Generic |
| `speckit-constitution` | Create or update the project constitution from interactive or provided principle inputs. Resolves the constitution-template through the preset/extension stack, writes to .specify/memory/constitution.md. Run after speckit-init. | Generic |
| `speckit-specify` | Create or update the feature specification from a natural language feature description. Resolves the spec-template, creates specs/NNN-\<slug\>/spec.md, and writes .specify/feature.json. Lazy-scaffolds .specify/ if absent. | Generic |
| `speckit-clarify` | Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec. Reads the active feature directory via check-prerequisites.sh. | Generic |
| `speckit-plan` | Execute the implementation planning workflow using the plan template to generate design artifacts (plan.md, research.md, data-model.md, contracts/, quickstart.md). Reads the active feature directory via setup-plan.sh. | Generic |
| `speckit-tasks` | Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts. Uses setup-tasks.sh which returns TASKS_TEMPLATE_CONTENT already composed. Every task follows strict checklist format - [ ] T001 [P?] [US?] Description with exact file path. | Generic |
| `speckit-analyze` | Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation. STRICTLY READ-ONLY — never edits files, only reports findings. | Generic |
| `speckit-checklist` | Generate a custom requirements-quality checklist for the current feature. Checklists are unit tests for requirements writing — they validate completeness, clarity, and consistency of requirements, NOT whether code works. Optional/parallel with analyze and implement. | Generic |
| `speckit-implement` | Execute the implementation plan by processing and executing all tasks defined in tasks.md. Runs phase by phase, marks completed tasks [x], honors [P] parallelism and dependency order, halts on failure. | Generic |
| `speckit-commit` | Stage and commit changes with a conventional commit message and an optional ticket tag. Human-gated — shows a full preview and requires explicit confirmation before running git commit. Never pushes, force-pushes, or amends. | Generic |

---

## coding-skills

| Skill | Purpose | Generic or Project-specific |
|-------|---------|----------------------------|
| `api-endpoint` | Scaffold a new FastAPI endpoint following this project's patterns. Use when adding a new route to src/api/endpoints.py. | **Project-specific** — targets `src/api/endpoints.py` in a specific FastAPI project |
| `architect` | Designs system architecture for complex features and services. Provide requirements, constraints, and references to existing patterns. | Generic |
| `code-review` | Review code changes against dev branch for logic errors, style violations, security issues, and architectural anti-patterns specific to this codebase. | **Project-specific** — references "this codebase" and assumes a `dev` branch convention |
| `code-reviewer` | Performs structured code review for pre-PR and pre-merge validation. Specify files to review and acceptance criteria. | Generic |
| `documentation` | Maintains current and consistent documentation across the codebase. Specify scope (pre-PR or end-of-day). | Generic |
| `explain-code` | Explains code with visual diagrams and analogies. Use when explaining how code works, teaching about a codebase, or when the user asks how the code works. | Generic |
| `frontend-slides` | Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic through visual exploration rather than abstract choices. | Generic |
| `local-setup` | Walk through setting up and running the ai-chat-bot project locally from scratch. Use when a developer asks how to run the project, set up their environment, or get started locally. | **Project-specific** — written for the `ai-chat-bot` project |
| `multi-plan` | Multi-model collaborative planning workflow. Generates and saves implementation plans without modifying production code. | Generic |
| `orchestrate` | Coordinates a multi-agent workflow with structured handoffs and a consolidated final report. | Generic |
| `plan` | Creates structured implementation plans for complex tasks. Provide requirements, constraints, and references to existing code. | Generic |
| `product-thinking-plan` | Product-thinking and user-value review for ToucanGrow LMS features. Use before proposing screens, database entities, APIs, or implementation tasks to ensure real user value is established first. | **Project-specific** — written for the ToucanGrow LMS product |
| `security-reviewer` | Performs dedicated security analysis for pre-PR and pre-merge validation. Specify files to review and security focus areas. | Generic |
| `sonarqube` | Set up, run, and manage the local SonarQube instance via Docker Compose. Use when asked to start SonarQube, analyze code quality, configure a project, or troubleshoot the local SonarQube setup. | **Project-specific** — set up for the SonarQube Docker Compose in `orchestration/core/sonarqube` |
| `staging-release` | Cut a staging release branch off staging, cherry-pick a batch of tickets from dev, verify it, and open the PR. Use when the user gives a list of ticket codes marked Ready for Staging, or asks to cherry-pick, promote, or deploy tickets from dev to staging. | **Project-specific** — assumes a specific `dev` / `staging` branch workflow with named ticket codes |
| `swarm` | Multi-agent orchestration workflow. Activate with `/swarm <task>` to plan, dispatch, and review work across codex, opencode, and sonnet executors. Planner/reviewer role = master agent. Implementation = worker agent or claude -p invocation. tmux NOT used; subprocess only. | Generic |
| `testing` | Help run tests or explain the test setup for this project. Use when the user asks about running tests, writing tests, test fixtures, or understanding the testing conventions. If a file or keyword is provided, run or explain tests for that target. | Generic |
| `test-suite` | Generate a comprehensive test suite for specified code. Use when asked to write tests for a file, class, or function in this project. | Generic |

### Legacy spec workflow (spec-driven-*)

> **These skills are being retired.** They are the previous generation of the spec-driven workflow. Existing projects using them will continue to work, but new projects should use the speckit family above. No new work is planned for these skills.

The legacy family includes: `spec-driven-init`, `spec-driven-specify`, `spec-driven-clarify`, `spec-driven-constitution`, `spec-driven-plan`, `spec-driven-tasks`, `spec-driven-tasks-to-issues`, `spec-driven-analyze`, `spec-driven-checklist`, `spec-driven-implement`, `spec-driven-converge`, and `spec-driven-samplefe`. Each has a `SKILL.md` in `coding-skills/spec-driven-<stage>/`.

---

## review-work

| Skill | Purpose | Generic or Project-specific |
|-------|---------|----------------------------|
| `code-critique` | Explain selected code for a beginner, then critique its limitations, readability, engineering principles, and improvement opportunities. | Generic |
| `code-review-bugs` | Review code changes for bugs, edge cases, security issues, resource leaks, API contract problems, caching issues, and convention violations. | Generic |
| `security-review` | Apply Vibe Coding Security Standards to generate, review, and harden application code against credential leakage, authorization bypasses, injection, shadow APIs, and AI-specific security failures. | Generic |

---

## study-and-documentation

| Skill | Purpose | Generic or Project-specific |
|-------|---------|----------------------------|
| `briefly-explain` | Briefly explain selected code in simple beginner-friendly language, including purpose, logic, syntax, and concise examples. | Generic |
| `database-check/` | Not a packaged skill. Holds a reference checklist (`schema-change-safety-review.md`) for safe schema changes. Copy and use manually. | Generic |
| `create-agents-md` | Generate or update a project-specific AGENTS.md by analyzing the target repository and injecting factual project context into the global coding rules template. | Generic |
| `eod-updates` | Create bulletized end-of-day update summaries for technical PMs and non-technical managers from files or changes the user mentions. | Generic |
| `explain-diff-html` | Create a rich, interactive, self-contained HTML explanation of a code change, diff, branch, commit, or pull request. Use when the user wants a visual technical walkthrough with beginner-friendly background, intuition, code-change analysis, diagrams, and an interactive quiz. | Generic |
| `explain-diff-markdown` | Create a rich Markdown and Notion explanation of a code change, diff, branch, commit, or pull request. Use when the user wants a beginner-friendly technical walkthrough with background, intuition, grouped code analysis, diagrams, callouts, and a multiple-choice knowledge check published as a Notion page. | Generic |
| `system-overview` | Analyze a repository and produce a comprehensive system-overview.md blueprint with architecture, schemas, operational path, security, directory structure, and key files. | Generic |
| `teach-explain` | Teach code to junior developers with big-picture explanation, syntax deep dive, code context, system design, annotated code, and learning checkpoints. | Generic |

---

## configurations

These directories do not contain runnable skills. They are configuration templates you copy into a project's root or `.claude/` folder.

| Directory | What it contains |
|-----------|-----------------|
| `configurations/global-coding-rules/` | Has a `SKILL.md` (name: `global-coding-rules`) plus `CLAUDE.md` and `AGENTS.md` templates. Use when generating repository-level agent instructions, coding standards, or change execution rules. Generic. |
| `configurations/ai-transform-service-rules/` | Has a `SKILL.md` (name: `ai-transform-service-rules`). **Project-specific** — targets CDS, IPAFFS, QC, QC3PL, RAG, parser/extractor providers in the AI Transform Service project. |
| `configurations/ai-orchestrator-lab/` | No SKILL.md. Top level has `README.md` and `CLAUDE.md`. The `claude-orchestration/` subdirectory contains `CLAUDE.md`, `ORCHESTRATION_GUIDE.md`, and `WORKSPACE_TEMPLATE.md`. Use as a reference configuration. |
| `configurations/ai-open-orchestrator-lab/` | No SKILL.md. Top level has `README.md`, `CLAUDE.md`, and `PLAN.md`. The `claude-orchestration/` subdirectory contains `CLAUDE.md`, `ORCHESTRATION_GUIDE.md`, and `WORKSPACE_TEMPLATE.md`. |
