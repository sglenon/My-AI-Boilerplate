# Global Coding Rules

You are my AI pair programmer. Optimize for correctness, clarity, maintainability, and safe integration with the existing codebase.

---

## 1. Think Before Coding

Before writing or changing code:

1. Restate the task in your own words.
2. Surface assumptions, ambiguities, and missing requirements.
3. If something important is unclear, ask focused questions instead of guessing.
4. For non-trivial work, give a brief plan before implementation.
5. Call out risks, tradeoffs, and safer alternatives when relevant.

Do not silently choose an interpretation when multiple reasonable interpretations exist.

---

## 2. Simplicity First

Write the minimum code that correctly solves the requested problem.

- No features beyond what was asked
- No speculative abstractions
- No unnecessary configurability
- Prefer readability over cleverness
- Prefer good naming over comments

If a simpler approach exists, say so.

---

## 3. Surgical Changes

Integrate with the existing codebase first.

- Inspect nearby code before writing anything new
- Follow existing patterns, naming, and structure
- Touch only what is necessary
- Do not refactor unrelated code
- Do not make drive-by improvements

Goal hierarchy:

**INTEGRATE > EXTEND > REFACTOR**

---

## 4. Goal-Driven Execution

Work toward verifiable outcomes.

- Define what success looks like
- Break work into steps when helpful
- Update/add tests if they exist
- Never claim code works without verification
- Do not fabricate outputs, logs, or results

---

## 5. Code Quality Standards

All code must be:

- Clear, concise, and idiomatic
- Readable and maintainable
- Modular with low coupling
- Defensive against invalid inputs
- Consistent with the existing codebase
- Strongly typed where applicable

Avoid:

- Overengineering
- Clever but opaque abstractions
- Premature optimization
- Broad exception handling without intent

---

## 6. Stability and Constraints

- Do not break existing functionality
- Do not introduce new dependencies without approval
- Respect performance, security, and deployment constraints

If a request is risky or unclear:
- Say so explicitly
- Propose safer alternatives

---

## 7. Change Tracking (Required)

For any meaningful code change, create or update:

**`changes_YYYY-MM-DD.md`**

Rules:

- If file exists → append
- If not → create

Include:

- Summary of changes
- Files modified
- Key decisions and rationale
- How to test locally
- Known risks or follow-ups

Exceptions:

- Skip for trivial fixes (formatting, lint-only, small typo)
- Skip if explicitly told not to

Goal: make every change understandable without reading the diff.

---

## 8. Linting and Formatting (Strict)

All code must conform to the repo’s linting and formatting standards.

For Python projects:

- Must pass: `black`, `ruff`, `flake8`, `mypy`, `pylint` (if present in repo)
- Follow naming conventions:
  - `snake_case` → variables/functions
  - `PascalCase` → classes
  - `UPPER_SNAKE_CASE` → constants
- Use explicit type hints
- Avoid `Any` unless justified

Rules:

- Match the repo’s existing lint configuration
- Do not introduce new lint tools unless already used
- Fix lint issues introduced by your changes only

---

## 9. Testing Policy

Do not assume or fabricate test results.

Instead:

- Provide exact steps to test locally
- Define expected outputs and failure signals
- Add/update tests if patterns exist
- Be explicit about what is not yet verified

---

## 10. Observability and Safety

When relevant, include:

- Logging (non-noisy, structured where applicable)
- Clear error handling
- Input validation and sanitization
- Security considerations

Differentiate:

- User/input errors vs system failures

---

## 11. Project-Specific Rules

This file defines global behavior.

Repo-specific rules (frameworks, async requirements, DBs, APIs, security policies, etc.) must be:

- Discovered from the codebase
- Followed strictly once identified

## 12. After code
- After every code session, WRITE ME a paragraphized summary of EVERYTHING you did. The problem you wanted to solve, the approach you made, the changes you implemented, etc. Make me be able to understand it from a high-level overview.

=====

PROJECT-SPECIFIC RULES

# Project Instructions — AI Transform Service Rules

> Internal working notes. **Do not commit.** This file is gitignored / opt-out by name.

This guide applies to work on CDS, IPAFFS, QC, QC3PL, RAG, parser/extractor providers, prompts, and downstream dataset/UI output paths. Use it before touching anything in `app/services/`, `app/prompts/`, shared helpers, provider abstractions, or dataset routes.

The goal is simple: fix the correct layer, preserve the existing output contract, and stop adding prompt/code rules that contradict each other.

---

## 1. Diagnose Before You Patch

Most bugs are not where they first appear. The pipeline has multiple stages:

`source file → parsing/OCR → markdown normalization → chunking/context isolation → batch chunking → extraction → post-processing/normalization → declaration JSON/output payload → dataset route/API → UI/CSV`

Before changing a prompt or code file, answer these first:

* **Where does the bad value first appear?** Trace from raw parsed markdown and raw LLM output forward. Do not assume the UI, CSV, or API response is the bug source.
* **Does it reproduce in isolation?** Compare single-file runs, batched runs, repeated runs, and another operating company/customer where possible.
* **Is the bug caused by parsed input, prompt instruction, extraction schema, post-processing, or route/UI mapping?**
* **What is the expected output contract?** Confirm field names, null behavior, array shape, ordering, and formatting before changing anything.

> **Example — CDS C-AO-I1274:** The UI showed 17 raw rows instead of 4. A first fix changed the dataset route to read from S3 declaration JSON, which made the count look correct. The real issue was earlier: the batched chunker treated a category/banner row as a line item. The route change masked the bug instead of fixing the broken layer.

---

## 2. Resolve Contradictions Before Adding Rules

Do not add a new prompt or code rule until you check whether it contradicts an existing one.

For every prompt change, search the same prompt file and nearby related prompt files for:

* Duplicate instructions that describe the same field differently
* Old examples that conflict with the new rule
* Field-specific rules that conflict with global rules
* Formatting examples that no longer match the expected output
* Business rules that were added for one customer but now read like global behavior

If there is a conflict, **resolve it in the same change**. Do not leave both instructions and hope the model chooses correctly.

### Precedence order when rules conflict

Use this order unless the project owner explicitly says otherwise:

1. **Schema/output contract** wins over wording preference.
2. **Field-specific rule** wins over a generic extraction rule.
3. **Business rule for the current service/customer/document type** wins over a broad cross-service rule.
4. **Latest accepted PR comment/change request** wins over older prompt text.
5. **Source document evidence** wins over inference.
6. **If still uncertain, return `null` rather than inventing a value.**

### Required cleanup when changing prompts

When adding or modifying a prompt rule:

* Remove or rewrite the old contradictory instruction.
* Update examples so they match the new rule.
* Keep field names, casing, null behavior, and list/object structure exactly consistent with the rest of the file.
* Do not introduce a new bullet style, header style, JSON style, or example format unless the whole file already uses it.
* Add one narrow example only if the rule is easy to misunderstand.

A prompt change is not done if the new instruction is correct but an old example still teaches the opposite behavior.

---

## 3. Prompts Must Match Local Formatting

Prompt files are code. Treat them as executable logic, not notes.

Before editing any `.tmpl` file:

* Match the existing section structure.
* Match the existing bullet style.
* Match the existing wording pattern for required/optional fields.
* Match the existing JSON/null formatting.
* Match the existing example style.
* Keep nearby rules in the same level of specificity.

Do not mix styles like:

* `Return null` in one rule and `leave blank` in another
* `Do not infer` in one field and `guess if likely` in another, unless the schema explicitly permits it
* `Progressive Defects` in one section and `progressive_defects` in another if the output schema expects exact display names
* Table examples with one header format and JSON examples with different field names

If the existing prompt is messy, clean the local section enough that the changed rule is not surrounded by contradictions.

---

## 4. No Hard-Coded Fixes In Code When the Rule Belongs in the Prompt

Customer-specific extraction behavior belongs in prompts when it is document-reading logic.

Good prompt-level rules:

* Treat a Selecta-style row such as `Mini famous 10.5cm` as a section/category banner if it has no article number and no declarable commercial fields.
* Treat bold grouping rows such as `**Pelargonium peltatum unrooted**` as headers unless the row also contains item-level commercial values.
* For CDS summary tables, use subtotal/summary rows only when the document clearly presents those rows as the declarable item grouping.
* For QC3PL, extract a field only from the evidence specified for that field; return `null` if the field cannot be confidently located.

Bad code-level fixes:

* Hard-coding a customer name into a parser or dataset route
* Dropping the first row of every table because one customer had a banner row
* Rewriting route output to hide extraction mistakes
* Adding post-processing that mutates declaration JSON shape for one case
* Inferring values from unrelated document-level references because a field is usually nearby

If a rule only makes sense for one customer and cannot be expressed narrowly, you are probably fixing the wrong layer or need a customer-scoped prompt rule.

---

## 5. No Global Fixes Unless the Bug Is Global

Do not change shared code to fix a service-specific or customer-specific issue.

Stay in the owning layer:

| Bug area                                                | First place to check                                                                                 |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| CDS item extraction                                     | `app/prompts/CDS/`, `app/services/cds/`                                                              |
| CDS declaration aggregation/packages/HS code behavior   | CDS extraction prompts, CDS normalization/business logic                                             |
| IPAFFS header/phyto/invoice extraction                  | `app/prompts/IPAFFS/`, `app/services/ipaffs/`                                                        |
| QC defect extraction                                    | `app/services/qc/`, QC prompts/output normalizers                                                    |
| QC3PL row extraction, pallet/traceability/defect fields | `app/services/qc3pl/`, QC3PL prompt library                                                          |
| Dataset/API display issue                               | `app/services/<service>/dataset/route.py` only after confirming extraction output is already correct |
| Shared provider behavior                                | Provider factory/normalizer only if multiple workflows share the same bug                            |
| Logging/auth/S3/common response behavior                | `app/helpers/`, `app/models/`, `app/middlewares/` only if truly shared                               |

A shared change is justified only when the bug affects shared behavior across services. Example: a logger crash in `app/helpers/utils.py` is global if every service can crash during log emission.

---

## 6. Preserve Output Contracts

Do not change field names, casing, object shape, list shape, or null behavior unless the schema/change request explicitly says so.

Before editing extraction logic, identify the expected contract:

* Exact field names
* Exact nested structure
* Array vs scalar behavior
* Number vs string behavior
* `null` vs empty string vs empty list
* Whether repeated values should be preserved, merged, deduplicated, or ordered
* Whether values are allowed to be inferred

### CDS-specific contract checks

For CDS work, verify:

* HS code fields use the actual HS/commodity code, not an internal code, item code, article code, F-code, or customer stock code.
* `Packages` follows the accepted CDS business rule for the document/customer; do not derive it from unrelated package-looking fields unless the rule says so.
* Summary rows and line-item rows are not mixed unless the prompt explicitly says how aggregation should work.
* Category banners/group headers are not extracted as declaration items.
* Declaration JSON shape stays compatible with existing downstream consumers.

### QC3PL-specific contract checks

For QC3PL work, verify:

* Required display field names stay exact: for example, `Cod. Pallet`, `Traceability`, `Pallet Number`, `Inspector Name`, `Brix`, `Temperature °C`, `No of Boxes Tested`, `No of Items Tested`, `Progressive Defects`, and `Non Progressive Defects`, if those are the schema names in the current prompt/output.
* Do not infer `Pallet Number` from client, reference, container/truck, total pallets, or shipment-level identifiers if the field rule says not to.
* Numeric arrays remain arrays when the contract expects arrays.
* Missing scalar values are `null` when unknown.
* Missing defect groups are empty lists when no defects are present.
* Progressive and non-progressive defects are not merged unless the prompt explicitly says they should be.
* Defect counts are taken from the row/section evidence, not invented from text descriptions.

---

## 7. Do Not Bypass the Pipeline

Fix the first broken layer. Do not patch a later layer to make the output look right.

Avoid:

* Injecting extraction results into the source dataset
* Adding a parallel write path for one case
* Reading declaration JSON from a route that is supposed to read source data unless the boundary is explicitly being redesigned
* Mutating declaration JSON shape from a read route
* Adding a UI/CSV workaround for an extraction bug

If extraction output is wrong, fix extraction. If declaration JSON is correct but the UI is wrong, fix the boundary that maps declaration output to UI output.

---

## 8. Parser, Chunker, Extractor, Normalizer: Keep Responsibilities Separate

Each stage has a job. Do not make one stage compensate for another unless the design explicitly calls for it.

| Stage                     | Owns                                                                | Should not own                                           |
| ------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------- |
| Parser/OCR                | Faithful markdown/table/page text representation                    | Business decisions about what is declarable              |
| Chunker/context isolation | Keeping related document sections together                          | Extracting final fields                                  |
| Batch chunker             | Splitting candidate item groups safely                              | Reinterpreting category headers as items                 |
| Extractor prompt          | Field-level reading rules and document-specific extraction behavior | Route-specific display fixes                             |
| Normalizer/post-processor | Type coercion, schema compatibility, deterministic cleanup          | New customer business rules not present in prompt/design |
| Dataset/API route         | Returning the correct stored/output data                            | Repairing bad extraction                                 |
| UI/CSV                    | Display/export formatting                                           | Changing business meaning                                |

When a change crosses these boundaries, explain why in the MR.

---

## 9. PR Comments Are Acceptance Criteria

Treat accepted PR comments as constraints for the next change, not as optional review notes.

Before opening an MR:

* Check every unresolved PR comment related to the touched file/service.
* Confirm the new change does not reintroduce an old rejected behavior.
* Include a short MR note explaining how each relevant comment was addressed.
* If two PR comments appear to conflict, resolve the conflict explicitly in the prompt/code and call it out in the MR description.
* If a comment changes a field rule, update examples and tests that still show the old behavior.

A PR comment is not addressed if the implementation passes one sample but leaves contradictory instructions in the prompt.

---

## 10. Testing Requirements Before Marking Done

Minimum checks:

* Reproduce the original bug on the un-fixed version.
* Run the fix on the failing input.
* Run the fix on at least one known-good input.
* Run the fix on a different customer/document shape when the changed prompt or code is shared.
* Compare raw LLM output, normalized output, declaration JSON/output payload, and UI/API output if the bug appears downstream.
* Read the full diff before opening the MR.

For prompt changes, also check:

* No contradictory instruction remains in the same prompt file.
* No example contradicts the new rule.
* Formatting matches nearby prompt sections.
* The output still validates against the expected schema.

For CDS changes, include at least one case that checks:

* Header/banner vs line item separation
* HS/commodity code correctness
* Package logic
* Summary/aggregation behavior, if relevant

For QC3PL changes, include at least one case that checks:

* Missing values become `null` or empty lists as required
* Defect grouping stays progressive vs non-progressive
* Pallet/traceability fields are not inferred from unrelated identifiers
* Numeric measurements preserve the expected array/scalar shape

---

## 11. Engineering Constraints That Apply Everywhere

* **No `.env`, credentials, tokens, or customer-data commits.** Use anonymized samples.
* **No `print()` in production code.** Use `logger.info`, `logger.warning`, or `logger.error`. Import logger with `from app.helpers.utils import logger`.
* **No skipping hooks** with `--no-verify` or similar. Fix the hook failure.
* **No `git add -A` or `git add .`.** Add files explicitly.
* **No amending pushed commits.** Make a new commit.
* **No force-pushing to `dev` or `main`.** Branches only, and only when you understand what will be overwritten.
* **No new top-level helper unless `app/helpers/` has been checked first.**
* **Do not commit working artifacts** such as `docs/superpowers/`, `PROJECT-INS-DONT-COMMIT.md`, raw JSON response dumps, screenshots, or temporary PDFs.

---

## 12. Branch and Commit Hygiene

Branch names:

* `fix/C-AO-I####-short-description`
* `feat/C-AO-I####-short-description`
* `chore/C-AO-I####-short-description`

Rules:

* Base on `dev`, not `main`, unless the release process says otherwise.
* Prefer one ticket per branch.
* Keep incidental fixes in separate commits.
* Mention incidental fixes clearly in the MR description.
* Commit format: `<type>: <subject>` plus a body explaining **why** the change is needed.

Good commit body:

```text
The previous prompt allowed category banner rows to be treated as line items when the banner appeared inside a table. This caused CDS item inflation for Selecta-shaped invoices. The updated rule scopes banner detection to rows without article numbers or commercial values and updates the example to match the new behavior.
```

---

## 13. Quick Reference — Where Things Live

| Concern                       | Location                                  |
| ----------------------------- | ----------------------------------------- |
| CDS extraction prompts        | `app/prompts/CDS/*.tmpl`                  |
| IPAFFS extraction prompts     | `app/prompts/IPAFFS/*.tmpl`               |
| QC extraction/service code    | `app/services/qc/`                        |
| QC3PL extraction/service code | `app/services/qc3pl/`                     |
| CDS service code              | `app/services/cds/`                       |
| IPAFFS service code           | `app/services/ipaffs/`                    |
| Dataset/route boundary        | `app/services/<service>/dataset/route.py` |
| Provider factories            | Parser/extractor provider factory modules |
| Models / DB / S3 access       | `app/models/`                             |
| Shared helpers                | `app/helpers/`                            |
| Auth middleware               | `app/middlewares/`                        |
| Entry point                   | `main.py`                                 |

---

## 14. When You Get Stuck

Do not add a flag, workaround, or customer-specific branch just to make the current sample pass.

Instead:

* Re-read the diagnosis section.
* Run the exact failing input locally with logging turned up.
* Save and compare raw parsed markdown, raw LLM output, normalized output, and final payload.
* Compare against a known-good run.
* Search the prompt for conflicting rules before adding a new one.
* Ask what the source of truth is: schema, accepted PR comment, business rule, source document, or UI expectation.

The right fix usually becomes obvious once you know which layer first produced the wrong value.
