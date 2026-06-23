---
name: test-suite
description: Generate a comprehensive test suite for specified code. Use when asked to write tests for a file, class, or function in this project.
---

Generate a comprehensive test suite for: $ARGUMENTS

## Project test conventions

- File location mirrors `src/`: e.g., tests for `src/ai_engine/intent/classifier.py` go in `tests/ai_engine/intent/test_classifier.py`
- `asyncio_mode = auto` — never write `@pytest.mark.asyncio`
- Pure unit tests (no DB) get `@pytest.mark.no_db`
- Use fixtures from `tests/conftest.py` — do not re-implement auth mocking

## Fixture selection guide

| Test type | Fixture to use |
|---|---|
| Unauthenticated endpoint | `client` |
| Authenticated endpoint | `user_client` or `make_user_client(user)` |
| DB-dependent logic | `session` |
| LLM processor (unit) | Mock the LLM, use `@pytest.mark.no_db` |
| Full integration | `staging_client` (skips if staging down) |

## What to generate

For each function/class under test, produce:

1. **Happy path** — normal input, expected output
2. **Edge cases** — empty input, boundary values, None/missing optional fields
3. **Failure modes** — invalid input raises correct exception, DB errors propagate correctly
4. **Async correctness** — verify no accidental blocking in async code
5. **For new intents/processors** — test that the processor is registered in `ProcessorFactory` and that its `NativeRouter` (if any) is registered in `ChatService._build_native_router()`

## Mocking patterns

```python
# Mock LLM calls
from unittest.mock import AsyncMock, patch

with patch("src.ai_engine.intent.classifier.ChatOpenAI") as mock_llm:
    mock_llm.return_value.ainvoke = AsyncMock(return_value=...)

# Mock HTTP calls to HR Hub / GraphQL
with patch("src.ai_engine.operational.hrhub_client.httpx.AsyncClient") as mock_client:
    mock_client.return_value.__aenter__.return_value.post = AsyncMock(...)

# Mock Pinecone
with patch("src.ai_engine.informational.processor.PineconeVectorStore") as mock_pc:
    mock_pc.return_value.similarity_search = AsyncMock(return_value=[...])
```
