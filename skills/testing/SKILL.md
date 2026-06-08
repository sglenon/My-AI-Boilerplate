---
name: testing
description: Help run tests or explain the test setup for this project. Use when the user asks about running tests, writing tests, test fixtures, or understanding the testing conventions. If a file or keyword is provided, run or explain tests for that target.
argument-hint: [file-or-keyword]
---

Help with testing for this project. If `$ARGUMENTS` is provided, run or focus on tests matching that file or keyword. Otherwise, explain the full test setup.

## Running tests

```bash
poetry run pytest                                          # all tests
poetry run pytest $ARGUMENTS                              # specific file or keyword
poetry run pytest -k "$ARGUMENTS"                         # match by keyword
poetry run pytest --no-header -q                          # quiet output
```

## Key conventions

- `asyncio_mode = auto` — never add `@pytest.mark.asyncio`; it is automatic
- `@pytest.mark.no_db` — mark pure unit tests to skip DB setup (faster)
- Tests mirror `src/` structure: `tests/ai_engine/`, `tests/services/`, `tests/schema/`
- Integration tests live in `tests/integration/`

## Fixtures (tests/conftest.py)

| Fixture | What it provides |
|---|---|
| `client` | Unauthenticated `AsyncClient` |
| `user_client` | Authenticated client (mocks `is_authenticated`) |
| `make_user_client(user)` | Authenticated client with a specific `UserSchema` |
| `session` | Async SQLAlchemy session → isolated test DB, auto-rollback |
| `staging_client` | Real staging auth; auto-skips if staging unreachable |

## Mocking patterns

- Mock `is_authenticated` via `monkeypatch.setattr("src.auth.HTTPBearer.__call__", fake_auth)` — see `user_client` fixture
- Mock `get_session` by patching `src.api.endpoints.get_session` and `src.services.ai_chat.get_session`
- For LLM calls, mock at the LangChain model layer (e.g., `ChatOpenAI`) to avoid real API calls in unit tests
