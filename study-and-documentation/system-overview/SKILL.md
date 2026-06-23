---
name: system-overview
description: Analyze a repository and produce a comprehensive system-overview.md blueprint with architecture, schemas, operational path, security, directory structure, and key files.
---

Analyze the repository at the current working directory and produce a comprehensive 'system-overview.md' file. Follow the exact structure, formatting conventions, and depth shown below. Do not omit sections. Use concise, factual technical writing.

---

### Required Structure (maintain this heading hierarchy)

**H1 Title** — `{Project Name} — Blueprint`

Meta line directly under the title: `Repo: {repo_name}` · `Updated: {YYYY-MM-DD}` · `Author: {author if known}`

One-sentence **Current priority** line summarizing the active work-stream.

---

**## 1. What We're Building**

- One-paragraph elevator pitch describing the system's purpose in plain language.
- A second short sentence clarifying the boundary (e.g., "We produce the JSON. Backend/API returns it.").
- **Decision / Answer table** (2 columns, `| Decision | Answer |`) covering:
  - Client-uploaded files vs. generated data
  - Code sharing with related repos
  - Current priority in one phrase
  - Legacy paths still present but bypassed
  - Experimental/alternate paths and their status

---

**## 2. Architecture**

- 2–4 bullet sentences describing the high-level stages.
- **ASCII flow diagram** using box-drawing characters (`│`, `├`, `└`, `►`, `▼`). Show:
  - External input at the top
  - Each major orchestrator / service as a labeled box
  - Named sub-components branching under their parent
  - Data artefacts flowing between stages
  - Terminal output at the bottom
- Keep the diagram left-aligned and annotate the purpose of each branch inline (e.g., `├── Summarizer                         compress history`)

---

**## 3. Graph Nodes** (or **Components / Pipeline Stages** if not a graph)

Break this into sub-sections per major stage or subsystem.

For each sub-section:
- State the pipeline definition file path if applicable.
- Provide a **mini ASCII flow diagram** for that stage if it has branching or loops.
- Provide a **Component table** with exactly these columns: `| Component | Purpose | Output |`
  - Component names in backticks.
  - Purpose: one concise sentence.
  - Output: data type or artefact name in backticks.

---

**## 4. Key Schemas**

List the 3–6 most important data models / DTOs / Pydantic classes.

For each schema:
- H3 heading with the class name in backticks.
- One sentence describing where it is used.
- Code block with the class definition (Python `dataclass` or Pydantic `BaseModel` preferred). Add inline comments on non-obvious fields.
- If the class is referenced from a specific function/method, note the caller in a short line above the code block.

Include a sub-section **"Output JSONs Condensed"** with 1–2 example JSON payloads (the actual shapes the system produces or consumes). Annotate each with a one-sentence description above the code block.

---

**## 5. Catalog / Domain Model** (adapt name to the repo's core registry)

- Identify the canonical source file and loader/model file.
- Provide the key class definitions in a code block (same style as Key Schemas).
- Provide a **summary table** listing the top-level entities in the catalog (e.g., bundles, features, modules) with their key attributes.
- Add a **Notes** bullet list covering aliases, precedence rules, or ownership boundaries.

---

**## 6. {Main Operational Path} (Current Operational Path)**

### Why This Path
- Table `| Approach | Status |` comparing the chosen implementation to at least two alternatives (e.g., pure LLM, fully hardcoded, legacy path, experimental path). State why the current one was selected.

### Stage 1 … Stage N
- Number each stage.
- Name the orchestrator, service, and pipeline definition file for each stage.
- Describe inputs, outputs, and side effects in 2–4 sentences.
- Mention error-handling posture explicitly (e.g., "failures are swallowed", "retries up to N", "best-effort overlay").

### Alternate / Legacy Paths
- If there are bypassed or legacy components, describe them in a dedicated sub-section.
- Note which newer component intentionally supersedes them and why the old one is still kept.

---

**## 7. Transport & Streaming**

- List the primary API endpoints as a short ASCII flow or as a code block with HTTP methods and paths.
- State the current transport mechanism (request/response JSON, SSE, WebSocket, etc.).
- Note any planned but not-yet-implemented streaming targets.

---

**## 8. Security & NFRs**

- Table `| Concern | Approach |` covering at minimum:
  - Secrets management
  - Auth mechanism
  - Prompt injection / input sanitization
  - Rate limiting
  - LLM-specific controls (temperatures, model selection)
  - Logging strategy
  - Resilience / failure modes
  - Validation strategy

---

**## 9. Directory Structure**

- ASCII tree of the repo.
- Limit depth to 2–3 levels.
- Add inline comments on every directory and on key files explaining what lives there.
- Group related subsystems under clear parent folders.

---

**## 10. Key Files Summary**

- Table `| Component | File |` mapping every major architectural component mentioned in earlier sections to its exact file path.
- Include orchestrators, services, pipeline definitions, loaders, registries, validators, middleware, and DI wiring.

---

### Formatting Rules (strict)

- Use **Markdown tables** for all tabular data; no bullet-list tables.
- Use **ASCII diagrams** for all flows; no Mermaid or other diagram syntax.
- Use **fenced code blocks** with language tags (`python`, `json`, `text`).
- Backtick all file paths, class names, function names, field names, and config keys.
- Keep prose sentences short and direct. One idea per sentence.
- Avoid marketing language. No "seamlessly", "leverage", "robust", "scalable".
- Prefer active voice.
- Do not include installation or setup instructions.
- Do not include a changelog or version history.

After generation, save the file to the specified directory by the user. Otherwise, save it to an existing docs/, or archive/, or documentation/ folder--depending on which exists.
