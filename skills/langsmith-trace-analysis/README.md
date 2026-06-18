# LangSmith Trace Analysis

Internal Codex skill for inspecting LangSmith traces without copying trace payloads by hand. It uses the official [`langsmith-mcp-server`](https://github.com/langchain-ai/langsmith-mcp-server).

## What It Provides

The official `langsmith-mcp-server` exposes the tools this skill relies on:

1. `list_projects`: list LangSmith projects, optionally filtered by name or reference dataset.
2. `fetch_runs`: fetch runs (traces, chains, tools, LLMs, parsers) from a project, with structured params (`run_type`, `error`, `is_root`), filter query language (`filter`, `trace_filter`, `tree_filter`), ordering, and char-budget pagination. Set `trace_id` to read a single trace tree.
3. `get_thread_history`: char-paginated message history for a conversation thread.

This supports questions like:

- Why did this extraction fail?
- Compare this failed trace with a successful one.
- Which agent, tool, parser, or LLM step produced the bad value?

## Setup

The server is configured in your MCP client, not run by hand. Provide LangSmith credentials via env (stdio) or headers (HTTP):

- `LANGSMITH_API_KEY` (required)
- `LANGSMITH_WORKSPACE_ID` (optional, for multi-workspace keys)
- `LANGSMITH_ENDPOINT` (optional, for self-hosted LangSmith)

### Option A: Local stdio via uvx (recommended)

```json
{
  "mcpServers": {
    "langsmith": {
      "command": "uvx",
      "args": ["langsmith-mcp-server"],
      "env": {
        "LANGSMITH_API_KEY": "lsv2_pt_your_key_here",
        "LANGSMITH_WORKSPACE_ID": "your_workspace_id",
        "LANGSMITH_ENDPOINT": "https://api.smith.langchain.com"
      }
    }
  }
}
```

Find the absolute `uvx` path with `which uvx` if your client requires it.

### Option B: Hosted HTTP-streamable server

```json
{
  "mcpServers": {
    "langsmith": {
      "url": "https://langsmith-mcp-server.onrender.com/mcp",
      "headers": { "LANGSMITH-API-KEY": "lsv2_pt_your_key_here" }
    }
  }
}
```

Optional headers: `LANGSMITH-WORKSPACE-ID`, `LANGSMITH-ENDPOINT`. The hosted instance targets LangSmith Cloud; for self-hosted LangSmith, run the server yourself.

## Tool Contracts

### `list_projects`

Input:

```json
{
  "project_name": "qc",
  "limit": 10,
  "more_info": false
}
```

Output (simplified, `more_info=false`):

```json
{
  "projects": [
    {
      "name": "qc3pl-prod",
      "project_id": "project-uuid"
    }
  ]
}
```

### `fetch_runs` (find root traces)

Input:

```json
{
  "project_name": "qc3pl-prod",
  "is_root": true,
  "error": true,
  "filter": "search(\"TRIMO\")",
  "order_by": "-start_time",
  "limit": 10,
  "page_number": 1
}
```

Output (char-budget paginated):

```json
{
  "runs": [
    {
      "id": "run-uuid",
      "trace_id": "trace-uuid",
      "parent_run_id": null,
      "name": "extract_declaration",
      "run_type": "chain",
      "status": "error",
      "start_time": "2026-06-08T10:00:00+00:00",
      "end_time": "2026-06-08T10:00:22+00:00",
      "error": "Validation failed",
      "inputs": { "...": "…" },
      "outputs": { "...": "…" }
    }
  ],
  "page_number": 1,
  "total_pages": 1,
  "max_chars_per_page": 25000,
  "preview_chars": 150
}
```

### `fetch_runs` (read one trace tree)

Input:

```json
{
  "project_name": "qc3pl-prod",
  "trace_id": "trace-uuid",
  "run_type": "parser",
  "error": true,
  "preview_chars": 80,
  "page_number": 1
}
```

Output:

```json
{
  "runs": [
    {
      "id": "run-uuid",
      "trace_id": "trace-uuid",
      "parent_run_id": "parent-run-uuid",
      "name": "validate_extraction",
      "run_type": "parser",
      "status": "error",
      "start_time": "2026-06-08T10:00:20+00:00",
      "end_time": "2026-06-08T10:00:22+00:00",
      "error": "Missing package_count"
    }
  ],
  "page_number": 1,
  "total_pages": 3,
  "max_chars_per_page": 25000,
  "preview_chars": 80
}
```

Iterate with `page_number = 2, 3, …` up to `total_pages` to read the rest of a large trace.

## References

- [LangSmith MCP Server](https://github.com/langchain-ai/langsmith-mcp-server)
- [LangSmith filter query language](https://docs.langchain.com/langsmith/filter-traces-in-application)
- [Query traces using the SDK](https://docs.langchain.com/langsmith/export-traces)
