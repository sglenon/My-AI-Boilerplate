---
name: qc-prompt-changes
description: Modify and verify QC extraction template changes. Use when the user asks to change, fix, or add extraction behavior for the QC pipeline using the live QC template and real files under `pdfs/qc/`.
---

Modify the QC extraction template the user identifies, then verify the change against real QC files before recommending promotion.

This skill is for **QC** only.

Do **not** use this for:

* `cds`
* `qc3pl`
* generic backend changes
* database or infrastructure changes

Before working, make sure if this is truly a QC issue.

## 1. Understand the requested QC change

Before editing anything, identify:

1. The customer / vendor / supplier affected.
2. The file or folder under `pdfs/qc/<folder>`.
3. The exact extraction issue.
4. The expected output.
5. Whether an `AGENT` name is required or can be auto-detected.

If the user provides screenshots, JSON outputs, issue descriptions, or expected values, use those as the source of truth.

Do not invent expected values. If expected behavior is unclear, state the ambiguity and proceed with the safest generalizable interpretation.

## 2. Fetch the current QC template

Always start from the live development QC template.

```bash
make get-qc-template OUTPUT=qc_template.current.json
```

Use a separate working copy for edits:

```bash
cp qc_template.current.json qc_template.edited.json
```

Do not edit the fetched original directly.

Do not copy secrets from the Makefile into the template or notes.

## 3. Inspect the relevant extraction context

Review the affected QC source folder:

```bash
ls pdfs/qc/<folder>
```

If the agent is unknown, list available QC agents:

```bash
make list-agents
```

Use the agent only when needed:

```bash
make dev-qc DIR=pdfs/qc/<folder> AGENT=<llama-agent-name>
```

If no agent is needed, allow auto-detection:

```bash
make dev-qc DIR=pdfs/qc/<folder>
```

## 4. Make the template change

Edit only `qc_template.edited.json`.

Rules:

* Make the change surgical.
* Do not rewrite unrelated customer sections.
* Do not alter global extraction behavior unless the issue is truly global.
* Generalize to the customer or document family, not to one sample file.
* Prefer adding clarification over replacing working instructions.
* Preserve the existing template structure, style, naming, and conventions.
* Do not hardcode values that only appear in one file unless the field is a fixed customer-specific mapping.
* Keep extraction rules tied to document evidence.

A good QC change explains:

* what field should be extracted
* where it should come from
* what labels or nearby context identify it
* what must not be used
* what to return when the value is absent or ambiguous

## 5. Validate the edited JSON

Before running extraction, confirm the edited template is valid JSON.

```bash
python -m json.tool qc_template.edited.json > /tmp/qc_template.validated.json
```

If this fails, fix the JSON before testing.

## 6. Establish the baseline result

Run the current/live QC extraction first, unless the user already provided a fresh baseline.

```bash
make dev-qc DIR=pdfs/qc/<folder>
```

Or with a known agent:

```bash
make dev-qc DIR=pdfs/qc/<folder> AGENT=<llama-agent-name>
```

Results are written to:

```text
results/qc/<folder>
```

Logs are appended to:

```text
dev.log
```

Use the baseline to confirm the issue exists before claiming the fix works.

## 7. Test the edited template locally

Use the edited template without pushing it.

```bash
make dev-qc-test-template DIR=pdfs/qc/<folder> FILE=qc_template.edited.json
```

Or with a known agent:

```bash
make dev-qc-test-template DIR=pdfs/qc/<folder> FILE=qc_template.edited.json AGENT=<llama-agent-name>
```

Review the output under:

```text
results/qc/<folder>
```

Also inspect `dev.log` for runtime errors, template parsing errors, agent errors, or extraction failures.

## 8. Compare baseline vs edited output

Verify the edited template fixes only the intended issue.

Check:

1. The target field now matches the expected value.
2. Previously correct fields stayed correct.
3. No unrelated rows disappeared.
4. No unrelated values changed unexpectedly.
5. Null handling is still correct.
6. The extraction remains evidence-based.
7. The result is generalizable beyond one exact sample.

If multiple files exist in the same customer folder, test all relevant files in that folder.

If the change could affect other QC customers, run at least one nearby regression folder.

## 9. Report the verification result

Return a concise summary with:

| Area            | Result                                     |
| --------------- | ------------------------------------------ |
| Template edited | `qc_template.edited.json`                  |
| Folder tested   | `pdfs/qc/<folder>`                         |
| Agent           | auto-detected or `<agent>`                 |
| Baseline issue  | What was wrong before                      |
| Fix result      | What changed after the edited template     |
| Regressions     | Any unrelated changes found                |
| Status          | Pass / Needs adjustment / Not safe to push |

Do not claim the change is safe unless the edited template was tested with `dev-qc-test-template`.

## 10. Push only after local verification

Never push directly to staging or production.

First run a dry-run push to development:

```bash
make put-qc-template FILE=qc_template.edited.json DRY_RUN=1
```

If the dry-run is clean and the user approves, push to development:

```bash
make put-qc-template FILE=qc_template.edited.json
```

Only push to staging with explicit approval:

```bash
make put-qc-template-staging FILE=qc_template.edited.json
```

Only push to production with explicit approval:

```bash
make put-qc-template-prod FILE=qc_template.edited.json
```

## 11. Optional environment checks

Use this when extraction fails due to connectivity or credentials:

```bash
make dev-db
```

This checks development connections using the configured dev AWS profile.

## 12. Common command reference

Fetch dev template:

```bash
make get-qc-template OUTPUT=qc_template.current.json
```

Fetch staging template:

```bash
make get-qc-template-staging OUTPUT=qc_template.staging.json
```

Fetch production template:

```bash
make get-qc-template-prod OUTPUT=qc_template.prod.json
```

Run QC extraction:

```bash
make dev-qc DIR=pdfs/qc/<folder>
```

Run QC extraction with agent:

```bash
make dev-qc DIR=pdfs/qc/<folder> AGENT=<llama-agent-name>
```

Test edited template:

```bash
make dev-qc-test-template DIR=pdfs/qc/<folder> FILE=qc_template.edited.json
```

Test edited template with agent:

```bash
make dev-qc-test-template DIR=pdfs/qc/<folder> FILE=qc_template.edited.json AGENT=<llama-agent-name>
```

List QC agents:

```bash
make list-agents
```

Dry-run push to dev:

```bash
make put-qc-template FILE=qc_template.edited.json DRY_RUN=1
```

Push to dev:

```bash
make put-qc-template FILE=qc_template.edited.json
```

Push to staging:

```bash
make put-qc-template-staging FILE=qc_template.edited.json
```

Push to production:

```bash
make put-qc-template-prod FILE=qc_template.edited.json
```

## 13. Safety rules

* Do not modify QC3PL prompts while working on QC.
* Do not push staging or production without explicit user approval.
* Do not skip local template testing.
* Do not commit or expose secrets from the Makefile.
* Do not use one-file-only hacks when a customer-level rule is needed.
* Do not broaden the change if a narrow fix solves the issue.
* Do not mark the task complete if `dev.log` shows relevant extraction errors.
