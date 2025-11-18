from agritech_core.config import Settings
from agritech_core.agents import AgritechOrchestrator
from agritech_core.rag import Document
from agritech_core.schemas import ChatRequest


def test_chat_flow_offline_mode():
    settings = Settings(llm_mode="offline", gemini_api_key=None)
    orchestrator = AgritechOrchestrator(settings=settings)
    orchestrator.ingest(
        [
            Document(doc_id="soil", text="Keep soil moist but not waterlogged.", metadata={"path": "soil"}),
            Document(doc_id="pest", text="Scout pests twice per week.", metadata={"path": "pest"}),
        ]
    )
    response = orchestrator.handle_chat(ChatRequest(message="How should I water my crops?"))
    assert response.reply
    assert response.tasks
    assert isinstance(response.citations, list)
