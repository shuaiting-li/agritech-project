"""FastAPI entrypoint for the Agritech assistant backend."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI

from agritech_core import AgritechOrchestrator, Settings, get_settings
from agritech_core.rag import Document, KnowledgeBase
from agritech_core.schemas import ChatRequest, ChatResponse, IngestRequest, IngestResponse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Agritech AI Assistant", version="0.1.0")
settings = get_settings()
orchestrator = AgritechOrchestrator(settings=settings)
_startup_ingested = False


def get_orchestrator() -> AgritechOrchestrator:
    return orchestrator


@app.on_event("startup")
def preload_documents() -> None:
    global _startup_ingested
    if _startup_ingested:
        return
    knowledge_dir = Path("data/knowledge_base")
    if not knowledge_dir.exists():
        logger.warning("Knowledge base directory %s not found", knowledge_dir)
        return
    docs = KnowledgeBase.load_markdown_dir(knowledge_dir)
    if not docs:
        logger.warning("No markdown documents discovered for initial ingestion")
        return
    chunks = orchestrator.ingest(docs)
    logger.info("Ingested %s knowledge chunks during startup", chunks)
    _startup_ingested = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
def ingest_documents(
    payload: IngestRequest, orchestrator: AgritechOrchestrator = Depends(get_orchestrator)
) -> IngestResponse:
    documents: list[Document] = []
    for idx, doc in enumerate(payload.documents):
        metadata = doc.metadata or {}
        doc_id = doc.doc_id or f"user-doc-{idx}"
        documents.append(Document(doc_id=doc_id, text=doc.text, metadata=metadata))
    chunks = orchestrator.ingest(documents)
    return IngestResponse(chunks_added=chunks)


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest, orchestrator: AgritechOrchestrator = Depends(get_orchestrator)
) -> ChatResponse:
    return orchestrator.handle_chat(request)
