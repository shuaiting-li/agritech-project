"""Pydantic schemas shared by the API and orchestrator."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentPayload(BaseModel):
    doc_id: str | None = Field(default=None, description="Optional document identifier")
    text: str
    metadata: dict[str, Any] | None = None


class IngestRequest(BaseModel):
    documents: list[DocumentPayload]


class IngestResponse(BaseModel):
    chunks_added: int


class PlannerAction(BaseModel):
    title: str
    detail: str
    priority: str = Field(default="medium")
    due: str | None = None


class ChatRequest(BaseModel):
    message: str
    location: str | None = None
    farm_type: str | None = None
    goals: list[str] | None = None
    force_refresh: bool = False


class ChatResponse(BaseModel):
    reply: str
    tasks: list[PlannerAction]
    citations: list[str]
