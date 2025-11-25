# Agritech Backend – Fair Review

**Reviewer:** Codex QA  
**Date:** _(auto-generated)_  
**Scope:** Backend MVP located in `app/` and `agritech_core/`

---

## Executive Summary

The delivered codebase accomplishes the stated goal of providing an MVP-quality LLM + RAG backend. FastAPI endpoints work, Gemini integration (with an offline stub) is implemented, and there is a lightweight retrieval pipeline with tests. The architecture is intentionally simple for prototyping, so several items called out below are trade-offs to revisit before production rather than outright defects.

---

## Key Strengths

- **Clear modularization.** Configuration, RAG utilities, LLM clients, and agents are separated cleanly (`agritech_core/*`).
- **Offline-friendly development.** Deterministic local embeddings/LLM stubs make it possible to run tests without Gemini credentials.
- **API ergonomics.** The `/ingest` and `/chat` routes expose concise JSON schemas and leverage Pydantic models for validation.
- **Documentation.** README now includes environment-variable defaults, setup steps, and API description.

---

## Findings

1. **Deprecated FastAPI startup hook (Low severity)**  
   - File: `app/main.py:27-42` still uses `@app.on_event("startup")`.  
   - Impact: Emits deprecation warnings on newer FastAPI versions; functionality is intact today.  
   - Recommendation: Migrate to a lifespan context manager when polishing for production. Not urgent for the current MVP.

2. **Process-wide orchestrator limits scaling (Medium severity for multi-worker deploys)**  
   - File: `app/main.py:17-24` instantiates a single `AgritechOrchestrator` and stores ingestion state in module-level globals.  
   - Impact: Works correctly for the single-process demo, but multi-worker servers (e.g., `uvicorn --workers 4`) would create separate in-memory knowledge bases, and there’s no persistence.  
   - Recommendation: Introduce a persistence layer or dependency-scoped orchestrator when horizontal scaling becomes necessary. For the present scope (single worker), this is an acceptable simplification.

3. **Chat request lacks length guard (Medium severity)**  
   - File: `agritech_core/schemas.py:31-36` only checks that `message` is a string.  
   - Impact: A very large payload could consume memory unnecessarily. The API already rejects blank strings via `str.strip()` in `KnowledgeBase.retrieve`, but there is no upper bound.  
   - Recommendation: Add `Field(..., min_length=1, max_length=4000)` (or similar) to `ChatRequest.message` before exposing the service publicly.

4. **Startup document ingestion errors aren’t surfaced (Low severity)**  
   - File: `app/main.py:27-42` swallows missing-directory cases with warnings but does not record whether ingestion failed.  
   - Impact: A deployment misconfiguration could leave the knowledge base empty without failing fast.  
   - Recommendation: Raise/propagate an exception or include a health-check indicator so operators notice missing data.

---

## Recommendations & Next Steps

1. **Validation & limits:** enforce message/chunk size limits and consider rate limiting prior to public exposure.
2. **Lifecycle updates:** move to FastAPI’s lifespan hook the next time the startup logic changes.
3. **State persistence:** evaluate a lightweight vector DB or serialized store so knowledge survives restarts and multi-worker deployments.
4. **Extended testing:** add integration tests hitting the FastAPI endpoints (perhaps via `httpx.AsyncClient`) once the API is stable.

Overall, the code is in good shape for an MVP demo that focuses on LLM + RAG functionality. Addressing the medium-severity findings will put it on firmer footing for subsequent milestones.
