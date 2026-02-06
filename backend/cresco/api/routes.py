"""API routes for Cresco chatbot."""

from fastapi import APIRouter, Depends, HTTPException, FastAPI
from pydantic import BaseModel

from cresco import __version__
from cresco.agent.agent import get_agent, CrescoAgent
from cresco.config import Settings, get_settings
from cresco.rag.indexer import index_knowledge_base, is_indexed

from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IndexRequest,
    IndexResponse,
)

router = APIRouter()

# In-memory storage for farm data
farm_data = {}

class FarmData(BaseModel):
    location: str
    area: float

app = FastAPI()

@router.post("/farm-data")
async def save_farm_data(farm: FarmData):
    try:
        # For simplicity, using a single key for now
        user_id = "default_user"
        farm_data[user_id] = {
            "location": farm.location,
            "area": farm.area
        }
        return {"message": "Farm data saved successfully", "data": farm_data[user_id]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/farm-data")
async def get_farm_data():
    user_id = "default_user"
    if user_id in farm_data:
        return {"data": farm_data[user_id]}
    else:
        raise HTTPException(status_code=404, detail="No farm data found for the user")

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Check API health and knowledge base status."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        knowledge_base_loaded=is_indexed(settings),
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    agent: CrescoAgent = Depends(get_agent),
) -> ChatResponse:
    """Send a message to the Cresco chatbot."""
    try:
        # Build the message, including farm data context if available
        message = request.message

        user_id = "default_user"
        if user_id in farm_data:
            farm_context = f"\n\n[Farm Data Context]:\nLocation: {farm_data[user_id]['location']}, Area: {farm_data[user_id]['area']} km²"
            message += farm_context

        result = await agent.chat(message)
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            tasks=result.get("tasks", []),
            conversation_id=request.conversation_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/index", response_model=IndexResponse, tags=["System"])
async def index_documents(
    request: IndexRequest,
    settings: Settings = Depends(get_settings),
) -> IndexResponse:
    """Index or re-index the knowledge base documents."""
    try:
        num_docs = await index_knowledge_base(settings, force=request.force_reindex)
        return IndexResponse(
            status="success",
            documents_indexed=num_docs,
            message=f"Successfully indexed {num_docs} document chunks",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")

# Include the router in the FastAPI app with the prefix `/api/v1`
app.include_router(router, prefix="/api/v1")
