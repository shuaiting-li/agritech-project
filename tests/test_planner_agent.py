import json
import pytest
from agritech_core.agents import PlannerAgent
from agritech_core.schemas import ChatRequest, PlannerAction
from agritech_core.llm import BaseLLMClient
from agritech_core.config import Settings


class MockLLM(BaseLLMClient):
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.last_prompt = None

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        self.last_prompt = prompt
        return self.response_text


def test_planner_agent_parsing_success():
    # Setup
    expected_json = json.dumps(
        [
            {"title": "Water Crops", "detail": "Water the maize", "priority": "high"},
            {"title": "Check Pests", "detail": "Look for worms", "priority": "medium"},
        ]
    )
    mock_llm = MockLLM(response_text=expected_json)
    settings = Settings()
    agent = PlannerAgent(llm=mock_llm, settings=settings)

    # Execute
    request = ChatRequest(message="I planted maize")
    actions = agent.build_actions(request, history="")

    # Verify
    assert len(actions) == 2
    assert actions[0].title == "Water Crops"
    assert actions[0].priority == "high"
    assert actions[1].title == "Check Pests"

    # Verify prompt contained key instructions
    assert "You are an agronomy task planner" in mock_llm.last_prompt
    assert "I planted maize" in mock_llm.last_prompt


def test_planner_agent_parsing_failure():
    # Setup - LLM returns garbage
    mock_llm = MockLLM(response_text="I am not sure what to do.")
    settings = Settings()
    agent = PlannerAgent(llm=mock_llm, settings=settings)

    # Execute
    request = ChatRequest(message="Hello")
    actions = agent.build_actions(request, history="")

    # Verify - Should return empty list, not crash
    assert actions == []


def test_planner_agent_markdown_cleanup():
    # Setup - LLM returns markdown code block
    json_content = json.dumps(
        [{"title": "Task", "detail": "Detail", "priority": "low"}]
    )
    markdown_response = f"```json\n{json_content}\n```"

    mock_llm = MockLLM(response_text=markdown_response)
    settings = Settings()
    agent = PlannerAgent(llm=mock_llm, settings=settings)

    # Execute
    request = ChatRequest(message="test")
    actions = agent.build_actions(request, history="")

    # Verify
    assert len(actions) == 1
    assert actions[0].title == "Task"
