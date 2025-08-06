import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from . import orchestrator
from .config import settings
from .instrumentation import configure_logging

# Configure logging and LangSmith tracing on startup
configure_logging()
# NOTE: LangSmith tracing is configured via environment variables like
# LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, etc.

logger = logging.getLogger(__name__)
app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    # Add other potential fields like image_url for multimodal search

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # This is a good place to initialize clients that can be reused,
    # like the OpenSearch and Bedrock clients, to leverage connection pooling.
    app.state.orchestrator = await orchestrator.RAGOrchestrator.create(settings)
    logger.info("Application startup complete. RAG Orchestrator initialized.")

@app.post("/search")
async def search(request: SearchRequest, http_request: Request):
    """
    Main endpoint for RAG-based search.
    Streams a response back to the client.
    """
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
        rag_orchestrator = http_request.app.state.orchestrator
        
        async def stream_generator():
            async for chunk in rag_orchestrator.stream_rag_response(request.query, request.user_id):
                yield chunk
        
        return StreamingResponse(stream_generator(), media_type="text/plain")

    except Exception as e:
        logger.exception(f"An error occurred during search for query: '{request.query}'")
        raise HTTPException(status_code=500, detail="An internal error occurred.")

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}