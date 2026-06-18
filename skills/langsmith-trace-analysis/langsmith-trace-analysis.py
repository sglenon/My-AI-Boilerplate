"""MCP server for searching and fetching LangSmith traces."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langsmith import Client
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("langsmith-traces-mcp")
client = Client()


FILTER_PRESETS = {
    "all": None,
    "errors": 'eq(status, "error")',
    "llm_runs": 'eq(run_type, "llm")',
    "tool_runs": 'eq(run_type, "tool")',
    "retriever_runs": 'eq(run_type, "retriever")',
    "parser_runs": 'eq(run_type, "parser")',
    "chain_runs": 'eq(run_type, "chain")',
    "prompts": 'eq(run_type, "prompt")',
}


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def serialize_dt(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def escape_filter_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def combine_filters(filters: list[str | None]) -> str | None:
    active_filters = [filter_value for filter_value in filters if filter_value]
    if not active_filters:
        return None
    if len(active_filters) == 1:
        return active_filters[0]
    return f"and({', '.join(active_filters)})"


def run_status(run: Any) -> str:
    status = getattr(run, "status", None)
    if status:
        return str(status)
    return "error" if getattr(run, "error", None) else "success"


def latency_ms(run: Any) -> int | None:
    start_time = getattr(run, "start_time", None)
    end_time = getattr(run, "end_time", None)
    if not start_time or not end_time:
        return None
    return int((end_time - start_time).total_seconds() * 1000)


def run_summary(
    run: Any,
    include_inputs: bool = False,
    include_outputs: bool = False,
) -> dict[str, Any]:
    summary = {
        "id": str(run.id),
        "trace_id": str(getattr(run, "trace_id", None) or run.id),
        "parent_run_id": (
            str(run.parent_run_id) if getattr(run, "parent_run_id", None) else None
        ),
        "name": run.name,
        "run_type": run.run_type,
        "status": run_status(run),
        "start_time": serialize_dt(getattr(run, "start_time", None)),
        "end_time": serialize_dt(getattr(run, "end_time", None)),
        "latency_ms": latency_ms(run),
        "error": getattr(run, "error", None),
        "tags": getattr(run, "tags", []) or [],
        "metadata": getattr(run, "metadata", {}) or {},
    }
    if include_inputs:
        summary["inputs"] = getattr(run, "inputs", None)
    if include_outputs:
        summary["outputs"] = getattr(run, "outputs", None)
    return summary


@mcp.tool()
def list_projects(name_contains: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List LangSmith projects, optionally filtered by project name."""
    projects = client.list_projects(name_contains=name_contains)

    return {
        "projects": [
            {
                "id": str(project.id),
                "name": project.name,
                "created_at": serialize_dt(getattr(project, "created_at", None)),
            }
            for project in list(projects)[:limit]
        ]
    }


@mcp.tool()
def search_traces(
    project_name: str,
    start_time: str | None = None,
    end_time: str | None = None,
    error: bool | None = None,
    query: str | None = None,
    raw_filter: str | None = None,
    limit: int = 10, # change depending on project
) -> dict[str, Any]:
    """Search root traces in a LangSmith project."""
    filters = []
    if query:
        filters.append(f'search("{escape_filter_value(query)}")')
    if raw_filter:
        filters.append(raw_filter)

    kwargs: dict[str, Any] = {
        "project_name": project_name,
        "is_root": True,
        "limit": limit,
    }
    if start_time:
        kwargs["start_time"] = parse_dt(start_time)
    if end_time:
        kwargs["end_time"] = parse_dt(end_time)
    if error is not None:
        kwargs["error"] = error

    filter_string = combine_filters(filters)
    if filter_string:
        kwargs["filter"] = filter_string

    runs = list(client.list_runs(**kwargs))

    return {
        "project_name": project_name,
        "filter": filter_string,
        "traces": [run_summary(run) for run in runs],
    }


@mcp.tool()
def fetch_trace(
    project_name: str,
    trace_id: str,
    run_type: str | None = None,
    status: str | None = None,
    name_contains: str | None = None,
    filter_preset: str = "all",
    raw_filter: str | None = None,
    include_inputs: bool = True,
    include_outputs: bool = True,
    limit: int = 100,
) -> dict[str, Any]:
    """Fetch all or filtered runs inside a LangSmith trace."""
    filters = []
    preset_filter = FILTER_PRESETS.get(filter_preset)
    if preset_filter:
        filters.append(preset_filter)
    if raw_filter:
        filters.append(raw_filter)
    if run_type:
        filters.append(f'eq(run_type, "{escape_filter_value(run_type)}")')
    if status:
        filters.append(f'eq(status, "{escape_filter_value(status)}")')
    if name_contains:
        filters.append(f'search("{escape_filter_value(name_contains)}")')

    select = [
        "id",
        "trace_id",
        "parent_run_id",
        "name",
        "run_type",
        "status",
        "start_time",
        "end_time",
        "error",
        "tags",
        "metadata",
    ]
    if include_inputs:
        select.append("inputs")
    if include_outputs:
        select.append("outputs")

    filter_string = combine_filters(filters)
    runs = list(
        client.list_runs(
            project_name=project_name,
            trace_id=trace_id,
            filter=filter_string,
            select=select,
            limit=limit,
        )
    )

    return {
        "project_name": project_name,
        "trace_id": trace_id,
        "filter": filter_string,
        "runs": [run_summary(run, include_inputs, include_outputs) for run in runs],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
