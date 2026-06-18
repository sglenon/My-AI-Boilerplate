---
name: 9ai-prompt-changes
description: Modify a vendor extraction prompt in the QC, CDS, IPAFFS, or QC3PL pipelines. Use when the user asks to change, fix, or add to a customer/vendor prompt for one of these systems.
---

Modify the vendor prompt the user identifies, then verify the change against real files.

## 1. Build context before editing

Read, in order:

1. The project overview for the relevant system in `archive/00-project-overviews/`.
2. The business logic in `archive/01-knowledge-library/`.
3. The issue / change description the user provided.
4. Any mapping documents in `archive/00-project-overviews/*`.
5. The current state of the target prompt file.

## 1.1 Before working! Ask yourself these:
1. Am I editing the correct pipeline (QC, QC3PL, CDS, IPAFFS)?
2. Can I surgically make vendor-specific fixes without creating global changes?

## 2. Make the modification

- **Generalize to the customer, not the file.** The prompt must work across different files from the same customer — the system is meant to be dynamic per customer, not hardcoded to one document.
- **Edit surgically.** Touch only the relevant section. Never modify other vendors' prompts or global/shared prompts.
- **Follow the prompt file's existing conventions** (structure, formatting, tone).
- Prompt files are executable logic — treat them like code.

## 3. Verify with the Makefile

1. Check the `Makefile` for the correct target and arguments.
2. Source PDFs live in `pdfs/{project}/*`.
3. Generated JSON output lands in `results/{project}/*`.
4. Compare the JSON results against the source PDFs to confirm correctness, accounting for any mapping document.

## 4. For Successful runs
For successful runs and no more prompt changes:
1. Run process 2 more times [for total of 3 runs], noting consistency.
  - Use the Make rename command for renaming previous runs, including dev.log
2. If all consistent, end process and report to user. 

## 5. Lessons learned — read this BEFORE you edit (saves the most time)

These are the traps that waste a run or silently break the change. Do them in order; don't skip because a step "looks obvious."

### 5.1 NEVER edit the active prompt in place — bump the version chain
Versions are filename-based and nothing is overwritten. There is a 3-link pointer chain you must follow and repoint, or your edit does nothing:

```
transform.manifest.json   ── "extraction" ─▶   extraction.manifest.vN.json
extraction.manifest.vN.json ── projects.{project}.batches.{batch}.extractor.business ─▶  extraction_logic.vX.Y.tmpl
```

Steps to ship a change (example: qc3pl business v2.10 → v2.11):
1. `cp extraction_logic.v2.10.tmpl extraction_logic.v2.11.tmpl` and edit the **copy**.
2. `cp extraction.manifest.v1.18.json extraction.manifest.v1.19.json`; in the copy set `business: "v2.11"` (bump its own `version` field too).
3. In `transform.manifest.json` repoint `extraction` to `./extraction/extraction.manifest.v1.19.json` (bump its `version`).
4. Confirm the live wiring before running: `dev.log` prints `Loaded manifests: ... extraction=<the vN you expect>`. If it shows the old manifest, your repoint didn't take.

Rollback = just point `transform.manifest.json` back at the old manifest. The old `.tmpl` files stay on disk.

### 5.2 Figure out WHICH file is WHICH vendor before touching anything
The ticket label (e.g. "OGL/DOLE") is not the filename order. Identify each PDF first:
- `pdftotext -layout <file>.pdf - | sed -n '1,120p'` and match the content (brand/logo line, supplier, defect column names, a known inspector name, a sample Brix list) against the vendor subsections already in the prompt. A unique value like an inspector name or traceability number nails it fast.
- The extractor identifies the vendor from document content too (e.g. a "Dole logo" line, the supplier field). So the `Customer` value in the output tells you which vendor rules fired.

### 5.3 "Empty / missing field" is usually a MISSING VENDOR RULE, not a parser bug
The engine applies only **global rules + the identified vendor's rules**. Global rules deliberately forbid fallbacks (e.g. "do not use `Size` as the defect denominator unless a vendor rule permits it"). So if a vendor has **no subsection** for a field, the model correctly emits nothing.
- Before blaming the parser, look at what it actually produced. The LlamaParse markdown is cached server-side — fetch it with the job id from `dev.log`:
  ```bash
  KEY=$(AWS_PROFILE=harvestlab-dev aws ssm get-parameter --name llamaCloudApiKey --with-decryption --query Parameter.Value --output text)
  curl -s -H "Authorization: Bearer $KEY" https://api.cloud.llamaindex.ai/api/parsing/job/<JOB_ID>/result/markdown | python -c "import sys,json;print(json.load(sys.stdin)['markdown'])"
  ```
- If the parsed markdown already contains the value/column/header (it usually does), the fix belongs in the **extraction prompt's vendor subsection**, not the parser. Headers can be in the text even when `pdftotext` drops them (rotated/image text) — trust the LlamaParse markdown, not `pdftotext`.

### 5.4 The QC3PL prompt is ONE shared file with a vendor subsection per field
"Edit surgically / don't touch other vendors" means: add or change the **`### <Vendor>` subsection under the relevant `## <Field>` heading** (e.g. `## Non Progressive Defects` → `### Dole`). Adding a brand-new vendor means adding its subsection under each field it needs (often just Defects + a row-grain entry; the other fields fall back to global rules). Do not create a separate file.

### 5.5 Write rules as a worked example, not just prose (critical for weaker models)
Weaker models follow a concrete `input → JSON output` example far more reliably than a paragraph. For every rule you add, include: the source values, the exact formula (`Count = round(Size * value, 2)`), and the resulting JSON. Name the columns to **exclude** explicitly (summary/`Avg.*` columns, maturity readings) — "extract the defects" is too vague; weaker models will grab averages and totals.

### 5.6 When comparing the 3 verification runs, diff only the ticket-relevant fields
Some fields are legitimately flaky run-to-run (e.g. vendor `Customer` identification when the doc has no clear branding). Don't fail consistency on those. Diff the field the ticket is about (e.g. the defect lists); call out any unrelated flake separately as out-of-scope rather than re-editing the prompt to chase it.

### 5.7 Run the slow report alone while iterating
A 36-page PDF re-parses on every run. While dialing in a fix, copy just the broken PDF into its own `pdfs/{project}/<tmp>/` folder and run that one to iterate fast; do the full folder only for the final 3 consistency runs.
