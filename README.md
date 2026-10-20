# Personal Trainer Agent

LangGraph-powered personal trainer with member auth, workout logging, RAG over fitness knowledge, and rule-based input/output guardrails.

**Primary product:** a full-viewport web chat (`Form`) served by FastAPI.  
**Secondary / dev path:** the interactive CLI in `main.py`.

## Layout

```
main.py                 # CLI (register / login / chat) — secondary
server.py               # FastAPI: trainer API + web UI
web/                    # Full-screen chat frontend
  index.html
  styles.css
  app.js
trainer/                # Domain package (graph, tools, guardrails, RAG)
prompts/                # System prompt template
data/                   # Local JSON stores + knowledge markdown
scripts/                # Measurement and smoke helpers
tests/                  # Pytest suite (no live model calls)
```

## Requirements

- Python 3.14+ (see `.python-version`)
- [uv](https://docs.astral.sh/uv/) for installs and runs
- `ANTHROPIC_API_KEY` in a local `.env` for model calls

## Setup

```bash
uv sync --group dev
cp .env.example .env   # then set ANTHROPIC_API_KEY
```

Rebuild the vector store after cloning (Chroma files are not committed):

```bash
uv run python -c "from trainer.knowledge_base import build_knowledge_base; build_knowledge_base()"
```

## Run the web app (primary)

```bash
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

- Log in with an existing member ID (for example from `data/users.json`), or register a new profile.
- Messages go through `POST /api/chat` → the existing LangGraph trainer (guardrails, tools, RAG).

### API used by the UI

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/login` | Verify member ID |
| `POST` | `/api/register` | Create member |
| `POST` | `/api/chat` | One trainer turn |
| `GET` | `/api/members/{id}` | Profile |
| `GET` | `/api/members/{id}/workouts` | Workout history |

Legacy aliases `/chat` and `/members/...` remain for older clients.

## CLI (secondary)

```bash
uv run python main.py
```

## Develop

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format .
```

Optional measurement:

```bash
uv run python scripts/measure_agent.py
```

## Notes

- Dependency source of truth is `pyproject.toml` + `uv.lock`.
- `data/users.json` and `data/workouts.json` are local demo stores; `data/chroma_db/` and `data/memory.db` are generated at runtime.
- The web UI is static files under `web/`, mounted by `server.py` — no separate Node build step.
