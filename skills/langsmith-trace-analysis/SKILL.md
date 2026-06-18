---
name: langsmith-trace-analysis
description: Inspect, debug, compare, and analyze LangSmith traces through the official langsmith-mcp-server. Use when Codex needs to list LangSmith projects, find root traces by project/date/error/filter, fetch trace run trees, identify failed or suspicious agent/LLM/tool steps, compare successful and failed traces, or explain trace evidence from LangSmith payloads.
---

# LangSmith Trace Analysis

Use this skill to investigate LangSmith traces without manually copying trace payloads into the conversation.

## Required Setup

This skill uses the official `langsmith-mcp-server` (https://github.com/langchain-ai/langsmith-mcp-server). Configure it once in the MCP client, then call its tools.

- Require `LANGSMITH_API_KEY` in the environment (or the `LANGSMITH-API-KEY` header for the hosted HTTP server).
- Set `LANGSMITH_WORKSPACE_ID` when the API key spans multiple workspaces, and `LANGSMITH_ENDPOINT` for self-hosted LangSmith.
- Preferred local run: `uvx langsmith-mcp-server` over stdio. See `README.md` for the full MCP client config.

## MCP Tools

- `list_projects(project_name=None, limit=5, more_info=False, reference_dataset_id=None, reference_dataset_name=None)`: find LangSmith projects. Use this first when the project name is unknown or approximate.
- `fetch_runs(project_name, limit=50, page_number=1, trace_id=None, run_type=None, error=None, is_root=None, filter=None, trace_filter=None, tree_filter=None, order_by="-start_time", reference_example_id=None, max_chars_per_page=25000, preview_chars=150)`: the primary tool for both finding root traces and reading a trace tree.
  - Find candidate root traces: set `is_root=true`, plus `error=true`, `filter`, and a narrow `order_by`/`limit`.
  - Read one trace: set `trace_id`; results are paginated by character budget, so iterate with `page_number` up to `total_pages`.
- `get_thread_history(thread_id, project_name, page_number, max_chars_per_page=25000, preview_chars=150)`: char-paginated chronological message history for a conversation thread.

Note: `fetch_trace_tool` and `get_project_runs_stats_tool` exist in the server source but are NOT exposed as MCP tools. Use `fetch_runs` instead.

## Investigation Workflow

1. Resolve the project with `list_projects` when needed.
2. Find root traces with `fetch_runs(is_root=true, ...)`; keep `limit` narrow and use `error=true` or a `filter` expression.
3. Read the trace tree with `fetch_runs(trace_id=...)`; for very large traces lower `preview_chars` and page through with `page_number`.
4. Identify the first failed run, then inspect its parent, children, and nearest LLM/tool/parser runs.
5. Compare failed and successful traces by aligning run names, order, timing, inputs, outputs, and errors.
6. Explain conclusions using only evidence present in fetched runs. Mark uncertain claims as hypotheses.

## Filter Guidance

The official server takes LangSmith filter query language (FQL) and structured params rather than presets:

- Isolate failing runs: `error=true` or `filter='eq(status, "error")'`.
- Inspect prompts and model behavior: `run_type="llm"` or `filter='eq(run_type, "llm")'`.
- Tool-call failures and unexpected external data: `run_type="tool"`.
- Schema, JSON, validation, or output parsing failures: `run_type="parser"`.
- Text match on a value: `filter='search("TRIMO")'`.
- Use `trace_filter` to constrain by the root run and `tree_filter` to match anywhere in the run tree.

## Analysis Output

Use this shape for trace investigations:

### Verdict

Correct / Incorrect / Needs more evidence

### What happened

Briefly describe the failure path or behavioral difference.

### Evidence from trace

Cite relevant run names, IDs, timestamps, errors, inputs, or outputs.

### Likely issue

State the most likely cause and distinguish it from weaker hypotheses.

### Next action

Name the specific code path, prompt, parser, validator, data source, or agent step to inspect next.
