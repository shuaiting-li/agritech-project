"""Domain agents and orchestrator for the Agritech assistant."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from .config import Settings, get_settings
from .llm import BaseLLMClient, build_llm
from .memory import ConversationMemory
from .rag import Document, KnowledgeBase, RetrievedChunk
from .schemas import ChatRequest, ChatResponse, PlannerAction

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Produces lightweight actionable tasks for the farmer."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_actions(self, request: ChatRequest) -> list[PlannerAction]:
        actions: list[PlannerAction] = []
        msg = request.message.lower()
        if "irrig" in msg or "water" in msg:
            actions.append(
                PlannerAction(
                    title="Check irrigation",
                    detail="Verify soil moisture levels and irrigate if the topsoil is dry.",
                    priority="high",
                )
            )
        if request.location:
            actions.append(
                PlannerAction(
                    title="Local weather review",
                    detail=f"Check today's weather for {request.location} before field work.",
                    priority="medium",
                )
            )
        if request.goals:
            for goal in request.goals:
                actions.append(
                    PlannerAction(
                        title="Goal follow-up",
                        detail=f"Progress next step for: {goal}",
                        priority="medium",
                    )
                )
        if not actions:
            actions.append(
                PlannerAction(
                    title="General field walk",
                    detail="Walk through the farm and capture any anomalies or pests.",
                    priority="low",
                )
            )
        return actions


@dataclass
class RAGResult:
    context: str
    citations: list[str]
    chunks: list[RetrievedChunk]


class RAGAgent:
    def __init__(self, knowledge: KnowledgeBase, settings: Settings) -> None:
        self.knowledge = knowledge
        self.settings = settings

    def search(self, query: str) -> RAGResult:
        hits = self.knowledge.retrieve(query, self.settings.rag_top_k)
        context_lines = []
        citations: list[str] = []
        for hit in hits:
            snippet = hit.text.replace("\n", " ")
            context_lines.append(f"[{hit.chunk_id}] {snippet}")
            source = str(hit.metadata.get("path") or hit.metadata.get("source_doc") or hit.chunk_id)
            citations.append(source)
        context = "\n".join(context_lines) if context_lines else "No supporting documents."
        return RAGResult(context=context, citations=citations, chunks=hits)


class ChatAgent:
    def __init__(self, llm: BaseLLMClient, memory: ConversationMemory, settings: Settings) -> None:
        self.llm = llm
        self.memory = memory
        self.settings = settings

    def build_prompt(
        self, request: ChatRequest, rag_result: RAGResult, actions: list[PlannerAction]
    ) -> str:
        history_block = self.memory.as_prompt_block()
        actions_block = "\n".join(f"- {act.title}: {act.detail}" for act in actions)
        system_prompt = (
            "You are an assistant agronomist called Lima supporting smallholder farmers. "
            "Provide detailed yet practical answers. "
            "Always cite evidence snippets using [chunk-id] references."
        )
        prompt = f"""{system_prompt}
Context from knowledge base:
{rag_result.context}

Conversation history:
{history_block}

Planner recommendations:
{actions_block}

Current user message: {request.message}
Respond with actionable guidance and cite relevant chunk IDs.
"""
        return prompt

    def respond(self, request: ChatRequest, rag_result: RAGResult, actions: list[PlannerAction]) -> str:
        prompt = self.build_prompt(request, rag_result, actions)
        reply = self.llm.generate(prompt)
        self.memory.add("user", request.message)
        self.memory.add("assistant", reply)
        return reply


class AgritechOrchestrator:
    def __init__(
        self,
        knowledge: KnowledgeBase | None = None,
        llm: BaseLLMClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.knowledge = knowledge or KnowledgeBase(self.settings)
        self.llm = llm or build_llm(self.settings)
        self.memory = ConversationMemory(max_turns=self.settings.max_history)
        self.planner = PlannerAgent(self.settings)
        self.rag_agent = RAGAgent(self.knowledge, self.settings)
        self.chat_agent = ChatAgent(self.llm, self.memory, self.settings)

    def ingest(self, documents: Iterable[Document]) -> int:
        return self.knowledge.ingest(documents)

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        actions = self.planner.build_actions(request)
        rag_result = self.rag_agent.search(request.message)
        reply = self.chat_agent.respond(request, rag_result, actions)
        return ChatResponse(reply=reply, tasks=actions, citations=rag_result.citations)
