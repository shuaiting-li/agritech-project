# Cresco – Copilot Instructions

## Architecture

Cresco is a RAG-powered agricultural chatbot for UK farmers: **Python/FastAPI backend** (`backend/`) and **React/Vite frontend** (`frontend/`).

### Backend (`backend/cresco/`)

| Layer | Key files | Purpose |
|---|---|---|
| **API** | `api/routes.py`, `api/schemas.py` | FastAPI router mounted at `/api/v1`. Pydantic v2 request/response models. |
| **Auth** | `auth/routes.py`, `auth/dependencies.py`, `auth/jwt.py`, `auth/users.py`, `auth/schemas.py` | JWT Bearer auth (HS256 via `pyjwt`). Passwords hashed with `bcrypt`. Users stored in JSON file (`data/users.json`). Registration is admin-only; login is public. |
| **Agent** | `agent/agent.py`, `agent/prompts.py` | LangGraph agent (`CrescoAgent`) with two tools: `retrieve_agricultural_info` (RAG) and `TavilySearch` (internet). Uses `InMemorySaver` checkpointer keyed by `user_id` for conversation memory. Azure OpenAI (primary) or generic providers via `init_chat_model`. |
| **RAG** | `rag/retriever.py`, `rag/indexer.py`, `rag/embeddings.py`, `rag/document_loader.py` | ChromaDB vector store (`"cresco_knowledge_base"` collection), Azure OpenAI embeddings, markdown document loading with filename-based category metadata. Chunks: 1500 chars, 200 overlap. |
| **Config** | `config.py` | `pydantic-settings` based; reads `.env` from **project root** (`env_file="../.env"` relative to `backend/`). |

**App factory**: `main.py` uses `create_app()` → mounts `auth_router` and `router` under `/api/v1`. CORS allows `localhost:5173` and `localhost:3000`.

**Singletons — two patterns**:
- `get_settings()`: `@lru_cache` — clear via `get_settings.cache_clear()` in tests.
- RAG/agent modules (`get_embeddings()`, `get_vector_store()`, `get_retriever()`, `get_agent()`): module-level `_variable = None` with `global`. Reset by setting `module._variable = None` before patching.

**Data flow**: User message → `POST /api/v1/chat` (requires Bearer token) → farm/weather context appended from in-memory `farm_data` dict (keyed by JWT `user_id`) → `CrescoAgent.chat()` → LangGraph agent invokes RAG tool → ChromaDB similarity search (k=5) → LLM generates answer. Agent parses `---TASKS---` JSON blocks for actionable farming tasks.

**Auth flow**: `POST /auth/login` returns JWT → all other endpoints (except `/health`) require `Authorization: Bearer <token>` via `get_current_user` dependency. Admin bootstrap: `uv run python scripts/create_admin.py <username> <password>`.

### Frontend (`frontend/src/`)

React 19 + Vite. **No TypeScript** (plain JSX). CSS Modules for layout (`layout/*.module.css`). API calls in `services/api.js` use native `fetch` (no axios).

- **Auth**: JWT stored in `localStorage` (`cresco_token`/`cresco_username`). `AuthPage` component gates app access. Auto-logout on 401/403 responses.
- **Response mapping**: Backend `{answer, sources, tasks}` → frontend `{reply, citations, tasks}` in `api.js`.
- **Rendering**: `react-markdown` + `remark-gfm` + `remark-math` + `rehype-katex`.
- **Key components**: `App.jsx` (state), `layout/` (Header, ChatArea, SidebarLeft, SidebarRight), `satellite.jsx` (Leaflet + `@turf/area`), `weather.jsx` (OpenWeatherMap).
- **Env vars**: `VITE_API_URL` (default `http://localhost:8000/api/v1`), `VITE_OPENWEATHER_API_KEY`.

## Development Commands

```bash
# Backend (run from backend/)
uv sync --extra dev                              # Install with dev deps
uv run pytest                                    # Run tests
uv run pytest --cov --cov-report=term-missing    # Tests + coverage (80% min enforced)
uv run ruff check . && uv run ruff format .      # Lint + format
uv run uvicorn cresco.main:app --reload --port 8000  # Dev server
uv run python scripts/index_documents.py         # Index knowledge base
uv run python scripts/create_admin.py <user> <pass>  # Bootstrap first admin

# Frontend (run from frontend/)
npm install && npm run dev    # Dev server (port 5173, CORS allows 5173 + 3000)
npm run build                 # Production build
npm run lint                  # ESLint
```

## Testing Conventions

- **Always use classes**: `class TestFeatureName:` — no bare test functions.
- **Docstring per test method** describing what it verifies.
- **File naming**: `test_<module>.py` mirrors source structure.
- **Async tests**: `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` needed.
- **Mock all external services**: patch at import paths (e.g., `patch("cresco.rag.embeddings.AzureOpenAIEmbeddings")`). Zero real API calls.
- **Reset singletons** before tests: `cresco.rag.embeddings._embeddings = None`.
- **API test fixtures** (`conftest.py`):
  - `client` — sync `TestClient`, auth bypassed via `app.dependency_overrides[get_current_user]`.
  - `auth_client` — sync `TestClient` with **real auth** but mock agent/settings. Patches `cresco.auth.users.get_settings` and `cresco.auth.jwt.get_settings` to use `mock_settings` with temp `users.json`.
  - `async_client` — `AsyncClient` with `ASGITransport`, auth bypassed.
  - All fixtures patch `cresco.api.routes.is_indexed` and call `app.dependency_overrides.clear()` on teardown.
- **Auth test helpers**: `_create_admin_and_get_token(mock_settings)` / `_create_regular_user_and_get_token(mock_settings)` — seed users directly and return JWTs for endpoint testing.

## Code Style

- Python: **Ruff** — 100 char lines, Python 3.12 target, rules `E, F, I, N, W`.
- Use `str | None` (PEP 604), not `Optional[str]`.
- Pydantic v2 models with `Field(...)` for all API schemas.
- Build system: `hatchling`.
- Frontend: ESLint, no TypeScript, functional React components with hooks.

## Key Conventions

- `.env` at **project root** (not in `backend/`).
- Knowledge base: markdown files in `backend/data/knowledge_base/`. `_categorize_document()` in `document_loader.py` maps filename keywords → categories (`"disease"` → `disease_management`, `"nutri"` → `nutrient_management`, etc.).
- Indexing batches: 100 docs, 1s delay between batches (rate-limit protection in `rag/indexer.py`).
- Retrieval tool uses `response_format="content_and_artifact"` — text to LLM, raw `Document` objects for source extraction.
- `uv` is the package manager (not pip). Always run backend commands via `uv run`.
