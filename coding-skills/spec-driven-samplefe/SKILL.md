---
name: spec-driven-samplefe
description: Turn the active Spec-Driven product specification into an interactive, frontend-only UX sample backed by realistic mock data, then iterate on it before backend planning. Use when the user invokes $spec-driven-samplefe after specifying or clarifying a feature, or asks for a clickable prototype, HTML mockup, UI exploration, design-inspired screen, or UX-first validation without backend implementation.
---

# Spec-Driven Sample FE

Create a realistic frontend sample from the active product spec. Test user value and the complete experience before producing backend contracts or implementation plans.

## Runtime bootstrap

Before any other step, resolve the sibling `spec-driven-init` skill directory and run:

```bash
python3 <spec-driven-init-directory>/scripts/init_project.py --project-root .
```

Parse the JSON result and continue only when `ready` is `true`. If the sibling skill is unavailable, stop and tell the user the complete Spec-Driven skill suite must be copied together.

## User input

```text
$ARGUMENTS
```

Treat non-empty arguments as design references, prototype constraints, or feedback for the current sample. Inspect any attached or accessible reference images before editing the sample.

## Guardrails

- Build frontend and UX only.
- Do not add or change backend routes, services, models, migrations, storage, seeds, jobs, or deployment configuration.
- Do not create final API contracts or a final database model. Derive them later with `$spec-driven-plan` after UX approval.
- Do not call an existing backend from the sample. Use deterministic mock data and local interaction handlers.
- Preserve server-side authorization as a future requirement. A role switcher demonstrates states; it does not implement security.
- Keep the sample isolated from production navigation, analytics, and normal user workflows unless the user explicitly asks otherwise.
- Update the product spec only when validated feedback changes scope, behavior, copy requirements, or acceptance criteria.
- Document high-risk technical dependencies without building the backend as a hidden prerequisite.
- If planning artifacts already exist, do not edit or delete them and do not treat their existence as UX approval.

## Workflow

### 1. Resolve the active feature

Run once from the repository root:

```bash
python3 .specify/scripts/python/check_prerequisites.py --json --paths-only
```

Parse `REPO_ROOT`, `FEATURE_DIR`, and `FEATURE_SPEC`.

- Stop and recommend `$spec-driven-specify` if the feature directory or `spec.md` does not exist.
- Load the full feature spec, `.specify/memory/constitution.md` when present, and the feature requirements checklist when present.
- Load all repository instructions governing files in scope.
- Inspect the frontend stack, package manifest, design tokens, shared components, layouts, route conventions, mock patterns, and tests.
- Reuse existing files under `FEATURE_DIR/ux/` and the current sample route on later iterations.

Do not require `plan.md` or `tasks.md`. This skill belongs between specification and technical planning.

### 2. Run the product gate

Create or update `FEATURE_DIR/ux/product-review.md` before writing UI code. Include:

1. **User Problem** — user, triggering situation, current workaround, frequency, and consequence.
2. **Value Hypothesis** — task or decision made easier and the observable result.
3. **Primary User Journey** — trigger, entry, information, action, feedback, and outcome.
4. **Data-to-Action Mapping** — important information, its meaning, the decision, and the available action.
5. **Role Impact** — only roles affected by work, access, responsibility, or decisions.
6. **Friction and Operational Cost** — steps, repeated work, notifications, maintenance, and shifted work.
7. **Edge Cases and Failure States** — first-time, empty, loading, error, missing, denied, duplicate, completed, overdue, and unresolved.
8. **Product Risks** — privacy, incorrect decisions, stale data, duplicate workflows, notification noise, misuse, and irreversible actions.
9. **Success Measures** — primary metric, supporting measures, negative effects, and task-based validation.
10. **Product Verdict** — choose `Build`, `Simplify`, `Merge`, `Defer`, or `Reject` and explain why.

Stop before UI implementation for `Defer` or `Reject`. Prototype the recommended scope for `Simplify` or `Merge`.

When several journeys have equal priority, choose one primary journey using value, frequency, and risk. Record the assumption and represent the others as smaller scenarios. Ask only when no safe default exists and the choice materially changes the product.

### 3. Define the experience

Create or update `FEATURE_DIR/ux/state-matrix.md`:

| Role | Scenario | Entry point | Information shown | Primary action | Feedback or outcome |
|------|----------|-------------|-------------------|----------------|---------------------|

Cover the normal journey and every relevant state from the product gate, including narrow screens. Make it clear what is happening, why it matters, what to do next, what follows the action, and who owns unresolved work. Prefer one clear primary action per state.

### 4. Choose the sample format

Prefer the repository's existing frontend stack. Use standalone HTML only when no usable frontend exists, the user explicitly requests HTML, or disposable visual comparisons are the goal.

Follow the project's route and component conventions. Put the sample in a clearly isolated prototype or development-only location and document the exact route. Reuse existing design tokens and components. Convert inspiration into explicit traits such as hierarchy, density, spacing, navigation, typography, color, or interaction behavior.

When direction is uncertain, create at most three small alternatives for the disputed area, not three complete applications.

### 5. Build the interactive sample

Implement the complete primary journey with working local buttons, forms, dialogs, navigation, validation, success feedback, and recovery paths.

Keep data access behind a frontend-facing interface or provider. Supply stable mock fixtures. Do not fetch real endpoints directly from components.

Add a development-only scenario control when useful. Include relevant roles and normal, empty, loading, error, missing, denied, completed, overdue, unresolved, desktop, and mobile scenarios. Use hostile fixtures such as long names, missing optional values, large counts, stale timestamps, repeated records, and conflicting states.

Meet the existing frontend quality bar: semantic elements, accessible names, keyboard access, visible focus, responsive primary actions, clear feedback, reduced-motion support, and no unnecessary dependency.

### 6. Record the sample and decisions

Create or update `FEATURE_DIR/ux/samplefe.md` with the route or file, files changed, mock scenarios, primary journey, design references, assumptions, feasibility risks, open decisions, and run or verification commands.

Create `FEATURE_DIR/ux/decisions.md` if missing. Append dated entries without deleting useful history:

```markdown
## YYYY-MM-DD — Decision title

**Decision**: What changed or was selected.
**Reason**: Evidence or feedback behind it.
**Impact**: Effect on the spec, sample, or future backend.
```

### 7. Verify the sample

Run the smallest relevant checks first, then the normal frontend lint, type, build, and focused interaction checks. When browser tools are available, inspect desktop and narrow-screen views and walk through important failure states.

If the normal end-to-end harness requires a real backend, authentication service, or seeded data, do not weaken it or add a global bypass. Use isolated frontend checks or a manual browser walkthrough and record the constraint.

Create or update `FEATURE_DIR/ux/validation.md` with the date, tasks attempted, expected and observed outcomes, friction, defects, product questions, decision, and next iteration. Label team review, automated checks, and representative-user validation accurately.

### 8. Apply iteration feedback

On later invocations:

1. Inspect the current behavior.
2. Classify feedback as visual, interaction, content, requirement, or feasibility feedback.
3. Change the smallest coherent part of the sample.
4. Update `decisions.md`.
5. Update `spec.md` only for real requirement or acceptance changes.
6. Re-run affected checks and update `validation.md`.

Never begin backend work merely because the sample looks complete.

### 9. Evaluate the UX gate

Mark the sample ready only when the approved product verdict, complete primary journey, roles, permission boundaries, non-happy states, mobile behavior, data-to-action mapping, task-based review, accepted risks, and spec updates are all recorded.

Write one result in `validation.md`:

- `UX gate: Ready for backend planning`
- `UX gate: Not ready — <reasons>`

Do not invoke `$spec-driven-plan` automatically. Let the user approve the experience first.

## Completion report

Report the active feature and spec, product verdict, sample route, UX artifacts, scenarios, checks, UX gate, risks, and next action: iterate with `$spec-driven-samplefe` or approve and continue with `$spec-driven-plan`.

## Done when

- The active spec, constitution, and project instructions were read.
- Product value was reviewed before screens were built.
- A frontend-only sample demonstrates the primary journey with mock data.
- Relevant failure states and mobile behavior are represented.
- UX artifacts and decisions are recorded under `FEATURE_DIR/ux/`.
- Relevant checks pass, or failures are reported with evidence.
- No backend implementation or final backend contract was added.
