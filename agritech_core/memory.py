"""Lightweight conversational memory."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, Literal


Role = Literal["system", "user", "assistant"]


@dataclass
class ConversationTurn:
    role: Role
    content: str


class ConversationMemory:
    """Keeps a rolling buffer of conversation turns."""

    def __init__(self, max_turns: int = 6) -> None:
        self.max_turns = max_turns
        self._history: Deque[ConversationTurn] = deque(maxlen=max_turns)

    def add(self, role: Role, content: str) -> None:
        self._history.append(ConversationTurn(role=role, content=content.strip()))

    def as_prompt_block(self) -> str:
        lines = [f"{turn.role.upper()}: {turn.content}" for turn in self._history]
        return "\n".join(lines)

    def dump(self) -> Iterable[ConversationTurn]:
        return list(self._history)
