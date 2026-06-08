---
name: api-endpoint
description: Scaffold a new FastAPI endpoint following this project's patterns. Use when adding a new route to src/api/endpoints.py.
disable-model-invocation: true
argument-hint: [method path - description]
---

Scaffold a new FastAPI endpoint in `src/api/endpoints.py` following established patterns.

Request: $ARGUMENTS

## Pattern to follow

All endpoints live in `src/api/endpoints.py` on `router = APIRouter(tags=["v1"])`.

**Standard authenticated endpoint with DB:**
```python
@router.get("/resource/{resource_id}/")
async def get_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserSchema = Depends(is_authenticated),
) -> schema.ResponseSchema:
    ...
```

**CRITICAL — the `/ai_chat/` exception:**
Do NOT add `db: AsyncSession = Depends(get_db)` to any endpoint that triggers a full LLM call. Use `get_session()` context manager inside the function body instead — `Depends(get_db)` holds the DB session open for the entire request (~30s–1min for LLM calls).

```python
async def my_llm_endpoint(...) -> ResponseSchema:
    async with get_session() as db:
        # short DB operations here
        pass
    # long LLM call here, no open DB session
```

## Checklist before finishing

- [ ] Response type is a Pydantic v2 schema from `src/schema/`
- [ ] `is_authenticated` dependency used if auth required
- [ ] No sync DB calls inside async function
- [ ] Raises `HTTPException` with appropriate status codes
- [ ] Uses `aget_object_or_404` from `src/utils/utils.py` for single-object fetches
- [ ] Follows `snake_case` naming, double quotes, max 120 chars per line
