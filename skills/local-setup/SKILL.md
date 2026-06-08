---
name: local-setup
description: Walk through setting up and running the ai-chat-bot project locally from scratch. Use when a developer asks how to run the project, set up their environment, or get started locally.
disable-model-invocation: true
---

Walk me through setting up and running the ai-chat-bot project locally from scratch. Cover each step in order:

1. **Prerequisites** — Check for existing venv first
   - If `venv/` directory exists and contains Python 3.10–3.11, use that venv
   - If no venv, check for Poetry and Python 3.10–3.11
   - If Poetry isn't installed but venv exists, proceed with venv

2. **Dependencies** — Install dependencies
   - Using venv: `venv/bin/pip install -e .` or ensure dependencies are installed
   - Using Poetry: `poetry install`

3. **Environment** — Create `.env` file
   - If `.env.template` exists, copy it to `.env` and show required variables
   - If no template, create minimal `.env` with placeholders:
     - `DATABASE_URL=postgresql+asyncpg://user:pass@127.0.0.1:5432/dbname`
     - `REDIS_URL=redis://localhost:6379/0`
     - `OPENAI_API_KEY`, `SECRET_KEY`, etc. (use placeholders if testing)
   - List all required variables from `src/conf.py` that must be filled

4. **Database Setup** — Set up PostgreSQL and Redis
   - **First, check for docker-compose**: If `docker-compose.yml` exists in repo, try Docker first:
     - Run `docker compose up -d db redis` (or similar based on compose file)
   - **If Docker fails or no compose file, use local DB**:
     - Check if PostgreSQL is running: `pg_isready`
     - Check if Redis is running: `redis-cli ping`
     - If not running, start local services or guide user to start them
     - **Create a project-specific database** (don't use default "postgres" DB):
       - Create user: `CREATE USER ai_chat_bot WITH PASSWORD 'ai_chat_bot_password';`
       - Create database: `CREATE DATABASE ai_chat_bot_db OWNER ai_chat_bot;`
       - Grant privileges: `GRANT ALL PRIVILEGES ON SCHEMA public TO ai_chat_bot;`
       - **Important**: Grant CREATEDB permission for tests: `ALTER USER ai_chat_bot WITH CREATEDB;`
     - Update `.env` with new DB credentials

5. **Run Migrations** — Apply database schema
   - Using venv: `venv/bin/alembic upgrade head`
   - Using Poetry: `poetry run alembic upgrade head`
   - Ensure run from project root directory

6. **Run the app** — Start the server
   - Using venv: `venv/bin/python main.py`
   - Using Poetry: `poetry run python main.py`
   - Note: Starts on port 8000; Swagger at `/api-docs/swagger`

7. **Verify** — Confirm app is running
   - Hit the health check endpoint and confirm it returns `{"status": "OK"}`
   - For testing, run: `PYTHONPATH=. venv/bin/pytest tests/ --tb=short`

If any step fails, diagnose the error and suggest a fix before continuing. Do not skip steps.

**Notes for local execution**:
- When using venv, always set `PYTHONPATH=/path/to/project:$PYTHONPATH` for pytest if the project isn't installed in editable mode
- Test failures related to OpenAI/Pinecone API connections are expected when using placeholder keys
