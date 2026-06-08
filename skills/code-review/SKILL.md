---
name: code-review
description: Review code changes against dev branch for logic errors, style violations, security issues, and architectural anti-patterns specific to this codebase.
disable-model-invocation: true
argument-hint: [branch-name or file(s)]
---

## Step 1 — Get the diff

If `$ARGUMENTS` is a branch name or empty, fetch and diff against dev:

```bash
git fetch --all
git --no-pager diff origin/dev..HEAD
```

If `$ARGUMENTS` is a file path, diff that file:

```bash
git --no-pager diff origin/dev..HEAD -- $ARGUMENTS
```

Analyze only what appears in the diff. Do not review unchanged code.

## Step 2 — High-level summary

One short paragraph — what this diff does (technical, no fluff).

## Step 3 — Issues

Report every issue found, sorted most → least critical. No praise. No positives. Issues only.

Format: `[SEVERITY] file:line — description`

Severities: `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` / `STYLE`

### What to check

**CRITICAL**
- Hardcoded secrets, API keys, tokens, or connection strings
- Auth changes in `src/auth.py` or `is_authenticated` → flag for mandatory human review
- SQL injection risk (raw queries without parameterization)
- Sync DB calls inside async endpoints
- `Depends(get_db)` on endpoints with LLM calls — must use `get_session()` context manager instead

**HIGH**
- New processor intent added without registering `NativeRouter` in `ChatService._build_native_router()`
- New `NativeRouter` adapter without updating `ProcessorFactory._routable_intents`
- Alembic migrations added for LangGraph checkpoint tables
- Bare `Exception` caught without logging + `# pylint: disable=broad-exception-caught`
- Code that should be async but isn't — blocking calls inside async functions, missing `await`, sync I/O
- N+1 query patterns — DB queries inside loops, repeated fetches that could be batched
- Unoptimized loops — nested iterations or repeated expensive operations that could be simplified

**MEDIUM**
- Missing `mypy` strict compliance in `src/` code
- Non-Pydantic v2 schemas in `src/schema/`
- New code paths without tests
- Useless or misleading comments — comments that restate the code, are outdated, or commented-out blocks

**LOW**
- Missing `@pytest.mark.no_db` on pure unit tests
- Wrong fixtures used in tests (`@pytest.mark.asyncio` not needed — `asyncio_mode = auto`)

**STYLE**
- Single quotes instead of double quotes
- Line exceeds 120 characters
- Missing trailing commas on multi-line collections
- `print()` instead of `logging.getLogger(__name__)`
- Logging uses f-strings instead of `%s` format
- Naming violations: `snake_case` functions/vars, `PascalCase` classes, `UPPER_CASE` constants
- Missing `from __future__ import annotations` when forward-reference type hints are used

## Step 4 — Verdict

End with one of:
- `APPROVED` — ready to merge
- `APPROVED WITH COMMENTS` — address issues before merge
- `REQUIRES CHANGES` — critical or high issues must be resolved
- `HUMAN REVIEW REQUIRED` — auth or security-sensitive changes detected
