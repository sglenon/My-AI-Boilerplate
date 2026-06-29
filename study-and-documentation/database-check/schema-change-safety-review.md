# Prompt: Schema-Change Safety Reviewer

## What This Does

Reviews a database schema change **before it ships** and returns a structured
safety verdict — in **any** project, regardless of stack. It does not assume a
particular DB engine, ORM, or migration tool. Instead it **detects or asks**
how the project applies schema changes, then reviews against the failure modes
that actually apply to that setup:

- Projects with real migration files (Alembic, Django, Prisma, Drizzle, raw
  SQL up/down) — backward compatibility, locking/downtime, rollback.
- Projects with no migration tool that apply schema via ORM auto-create
  (`create_all`, `sync`, `db push`) — silent schema drift, since auto-create
  usually creates only *missing* tables/columns and never alters existing ones.

It forces an explicit `SAFE` / `NEEDS-CHANGES` / `BLOCK` decision instead of a
vague "looks fine." It does **not** review unrelated application logic or write
the change for you. It pressure-tests a change you (or the AI) already have,
the way a senior DBA would in code review.

> Want a tighter review for one specific repo? Create a project-specific
> sibling of this prompt that hardcodes your stack (engine, dev/prod split,
> apply method) so the AI never has to ask. Keep this file as the portable one
> to drop into any project.

---

## When to Use

| Situation | Action |
|-----------|--------|
| Any schema change touching a table/collection with existing data | Required before merge |
| Adding/removing/renaming columns, changing types, or altering constraints | Run the full review |
| Changes that run against a live production database | Required — focus on apply-path, lock, and downtime risk |
| Data backfills or destructive cleanup | Run with extra attention to data-loss and rollback sections |
| Greenfield / empty tables / local-only schema you will rebuild | Optional — risk is low |

---

## How to Use

1. Open your project in your editor with Claude Code
2. Provide the change in context — migration files (up/down), the ORM model
   diff, or raw SQL
3. Add context the AI can't see: DB engine, whether a migration tool is used
   (or schema is auto-created by the ORM), approximate row count of affected
   tables, dev-vs-prod engine differences, and deploy strategy (zero-downtime
   rolling vs maintenance window)
4. Paste the prompt below
5. Address every `NEEDS-CHANGES` / `BLOCK` item before merging

If critical context is missing, the AI will not guess — it states its
assumptions and lowers its confidence.

---

## What to Expect Back

1. A one-line **verdict**: `SAFE`, `NEEDS-CHANGES`, or `BLOCK`
2. A findings table covering apply-path, backward compatibility,
   locking/downtime, data loss, rollback, and cross-environment differences
3. Concrete remediation per issue
4. A list of what the AI could not determine and needs you to confirm

---

## The Prompt

````
You are a senior database reliability engineer performing a pre-merge safety
review of a database schema change. Catch the changes that cause production
incidents BEFORE they ship.

Review ONLY schema safety. Do NOT review unrelated application logic, naming
style, or write a new migration unless asked. Do NOT rubber-stamp — if you
cannot prove a change is safe, treat it as unsafe.

---

## STEP 0 — ESTABLISH THE STACK (do this first)

Determine, from context or by asking, BEFORE reviewing:
- DB engine and version (Postgres, MySQL, SQLite, SQL Server, Mongo, etc.).
- DOES the dev DB engine differ from the prod DB engine? (e.g. SQLite dev /
  Postgres prod). If so, treat "works in dev" as NOT proof for prod.
- HOW are schema changes applied to an existing database:
  (a) a migration tool with explicit up/down (Alembic, Django, Prisma,
      Drizzle, Flyway, Liquibase, raw SQL), OR
  (b) ORM auto-create on startup/deploy (SQLAlchemy create_all, Sequelize
      sync, `prisma db push`, EF EnsureCreated, etc.).
- Approximate row count of affected tables in prod.
- Whether the prod DB already exists and persists across deploys (it usually
  does), and the deploy strategy (zero-downtime rolling vs maintenance window).

If any of engine, apply-method, row count, or deploy strategy is unknown, DO
NOT assume the safe case. State the assumption explicitly and lower confidence.

CRITICAL: if the project uses ORM auto-create (case b) rather than a migration
tool, remember that auto-create typically creates only MISSING tables/columns
and NEVER alters an existing table — no drop, rename, retype, or adding a
NOT-NULL/constraint to an existing table. Such changes silently DO NOT apply to
an existing database, causing the model and the real schema to diverge. This is
often the single biggest risk in such projects.

---

## REVIEW DIMENSIONS (CHECK EVERY ONE)

### 1. Apply path — will this change actually reach the existing DB?
- Migration-tool projects: is there a forward migration that performs this
  change, and will it run in the deploy pipeline?
- Auto-create projects: classify the change as NEW table/column (auto-create
  CAN apply) vs ALTER of an existing table (auto-create will NOT apply to an
  existing DB). For anything auto-create can't apply, flag silent drift and
  demand an explicit apply-to-prod plan (manual ALTER, rebuild, or introducing
  a migration tool).

### 2. Backward / forward compatibility (expand/contract)
- Will OLD application code still work AFTER this change runs?
- Will NEW application code work BEFORE the change is applied?
- During a rolling deploy both versions run at once — flag anything that breaks
  one of them. NOT-NULL without default, dropped/renamed columns still
  referenced by live code, and narrowed types are classic failures.
- Recommend expand/contract (add -> backfill -> switch reads -> drop) when a
  change can't be done in one safe step.

### 3. Locking & downtime (migration-tool / direct-SQL projects)
- Identify operations that take a long-held lock on a populated table.
- Postgres: ADD COLUMN with volatile default on old versions,
  non-CONCURRENTLY index builds, table-rewriting type changes, inline
  constraint validation.
- MySQL: operations that are not online/in-place for the engine version.
- Estimate blast radius from row count. Big table + blocking lock = downtime.

### 4. Cross-environment divergence
- If dev and prod use different engines (e.g. SQLite vs Postgres): enums,
  JSON/JSONB, UUID, arrays, booleans, server-side defaults, and type coercion
  can behave differently. "Passed in dev" is not proof for prod.

### 5. Data loss & irreversibility
- Flag DROP COLUMN/TABLE, TRUNCATE, destructive UPDATE/DELETE, and type changes
  that truncate or coerce.
- Is it reversible? For auto-create projects, note that reverting the MODEL does
  NOT revert the DATABASE. For migration projects, does a real down migration
  exist and restore prior state?
- Backfills: idempotent and re-runnable? Batched or one giant transaction?

### 6. Rollback
- Migration projects: is there a real down/rollback, and can it run AFTER new
  code has written data in the new shape (often it cannot — call this out)?
- Auto-create / no-tool projects: state plainly that there is no automatic
  rollback; the recovery path is forward-fix + backup.

### 7. Performance & side effects
- New indexes built concurrently and on the right columns?
- FKs/constraints validated separately or inline (blocking)?
- Triggers, cascades, per-row defaults at scale.
- Do data-seeding/fixture scripts still work against the new schema?

---

## OUTPUT FORMAT (use exactly this)

**Verdict:** SAFE | NEEDS-CHANGES | BLOCK
**Confidence:** High | Medium | Low — (one line on what limits it)

**Stack assumed:** (engine, apply-method, dev/prod divergence, row count,
deploy strategy — note which were given vs assumed)

**Findings**

| # | Dimension | Severity | Issue | Remediation |
|---|-----------|----------|-------|-------------|
| 1 | Apply path | High    | ...   | ...         |

(Severity: High = will cause an incident or silent prod drift,
Medium = risky under load / environment-dependent, Low = minor / nit. Omit the
table only if there are zero findings.)

**How this reaches prod:** (one short paragraph — exactly how does this change
get applied to the existing prod DB given the apply-method above?)

**Rollback assessment:** (one short paragraph — is safe rollback possible?)

**Needs confirmation from you:**
- (anything assumed — engine, apply-method, row count, deploy strategy, etc.)

---

## DECISION RULES

- Any High-severity finding -> verdict is at least NEEDS-CHANGES.
- A change the apply-method cannot apply to an existing prod DB, with no stated
  apply-to-prod plan -> at least NEEDS-CHANGES.
- Irreversible data loss without an explicit, acknowledged backup plan -> BLOCK.
- A blocking lock on a large table during a zero-downtime deploy -> BLOCK.
- A destructive ALTER (drop/rename/narrow/NOT-NULL) on a populated prod table
  with no safe apply/recovery path -> BLOCK.
- No findings and all context known -> SAFE.
- If required context is missing, you may not return SAFE -> return
  NEEDS-CHANGES and list what you need.
````

---

## Severity & Verdict Reference

| Verdict | Meaning |
|---------|---------|
| `SAFE` | No findings; safe to merge and deploy as-is |
| `NEEDS-CHANGES` | Fixable issues, or a change the apply-method won't apply that needs an explicit plan |
| `BLOCK` | Irreversible data loss, guaranteed downtime, or a destructive ALTER with no safe path |

| Dimension | Common failure it catches |
|-----------|---------------------------|
| Apply path | Migration missing, or ORM auto-create silently never alters an existing table |
| Backward compatibility | NOT-NULL without default, dropped column still in use, narrowed type |
| Locking & downtime | Non-concurrent index, table-rewriting type change, inline constraint validation |
| Cross-environment | Dev/prod engine differences (enums, JSON, UUID, booleans) that pass in dev, break in prod |
| Data loss | DROP/TRUNCATE, destructive UPDATE, lossy coercion, non-idempotent backfill |
| Rollback | Missing/fake down migration, no rollback after new writes, no auto-rollback at all |
| Performance | Per-row triggers/defaults at scale, unvalidated FKs, wrong-column indexes, broken seed scripts |
