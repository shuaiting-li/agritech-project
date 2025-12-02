"""Domain agents and orchestrator for the Agritech assistant."""

from __future__ import annotations

import json
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
    """Produces lightweight actionable tasks for the farmer using LLM."""

    def __init__(self, llm: BaseLLMClient, settings: Settings) -> None:
        self.llm = llm
        self.settings = settings

    def build_actions(self, request: ChatRequest, history: str) -> list[PlannerAction]:
        system_prompt = (
            "You are an agronomy task planner. Your goal is to identify actionable tasks for the farmer based on their messages.\n"
            "Rules:\n"
            "1. If the user mentions planting a crop (e.g., 'I planted maize', 'sowed beans') in the history or current message, "
            "YOU MUST generate recurring tasks for watering and fertilizing.\n"
            "2. For other farming activities, generate relevant follow-up tasks.\n"
            "3. If the user provides a location, suggest checking the weather.\n"
            "4. Output MUST be a valid JSON list of objects with keys: 'title', 'detail', 'priority' (low, medium, high).\n"
            "5. Do not output any text other than the JSON.\n"
        )

        user_context = f"Location: {request.location}\n" if request.location else ""

        prompt = f"""{system_prompt}

Conversation History:
{history}

Current Message: {request.message}
{user_context}

Generate the JSON list of tasks:
"""
        try:
            response = self.llm.generate(prompt)
            # Clean up markdown code blocks if present
            cleaned_response = (
                response.replace("```json", "").replace("```", "").strip()
            )
            if not cleaned_response:
                return []

            data = json.loads(cleaned_response)

            actions = []
            for item in data:
                # Ensure priority is valid
                if "priority" not in item:
                    item["priority"] = "medium"
                actions.append(PlannerAction(**item))
            return actions
        except Exception as e:
            logger.warning(f"Failed to generate plan with LLM: {e}")
            # Fallback to basic actions if LLM fails
            return []


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
            source = str(
                hit.metadata.get("path")
                or hit.metadata.get("source_doc")
                or hit.chunk_id
            )
            citations.append(source)
        context = (
            "\n".join(context_lines) if context_lines else "No supporting documents."
        )
        return RAGResult(context=context, citations=citations, chunks=hits)


class ChatAgent:
    def __init__(
        self, llm: BaseLLMClient, memory: ConversationMemory, settings: Settings
    ) -> None:
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

    def respond(
        self, request: ChatRequest, rag_result: RAGResult, actions: list[PlannerAction]
    ) -> str:
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
        self.planner = PlannerAgent(self.llm, self.settings)
        self.rag_agent = RAGAgent(self.knowledge, self.settings)
        self.chat_agent = ChatAgent(self.llm, self.memory, self.settings)

    def ingest(self, documents: Iterable[Document]) -> int:
        return self.knowledge.ingest(documents)

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        history = self.memory.as_prompt_block()
        actions = self.planner.build_actions(request, history)
        rag_result = self.rag_agent.search(request.message)
        reply = self.chat_agent.respond(request, rag_result, actions)
        return ChatResponse(reply=reply, tasks=actions, citations=rag_result.citations)
