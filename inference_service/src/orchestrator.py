import asyncio
import logging
from typing import AsyncGenerator
from langsmith import traceable

from . import retriever, reranker, generator, guardrails, query_transformer
from .config import Settings

logger = logging.getLogger(__name__)

class RAGOrchestrator:
    """Orchestrates the end-to-end RAG pipeline asynchronously."""

    def __init__(self, settings: Settings, retriever_client, reranker_client, generator_client, transformer_client):
        self.settings = settings
        self.retriever = retriever_client
        self.reranker = reranker_client
        self.generator = generator_client
        self.transformer = transformer_client

    @classmethod
    async def create(cls, settings: Settings):
        """Asynchronously create an instance of the orchestrator."""
        # Initialize clients for dependencies
        retriever_client = retriever.HybridRetriever(settings.opensearch_host)
        reranker_client = reranker.SageMakerReranker(settings.reranker_endpoint_name)
        generator_client = generator.BedrockGenerator(settings.generator_model_id)
        transformer_client = query_transformer.QueryTransformer(settings.hyde_model_id, settings.redis_host)
        return cls(settings, retriever_client, reranker_client, generator_client, transformer_client)

    @traceable(name="stream_rag_response")
    async def stream_rag_response(self, query: str, user_id: str) -> AsyncGenerator[str, None]:
        """Full asynchronous RAG pipeline with streaming."""
        
        # 1. Input Guardrails & Transformation (can be run concurrently)
        guarded_query_task = guardrails.apply_input_guardrails(query)
        transformed_query_task = self.transformer.transform_query(query)
        
        guarded_query, transformed_query = await asyncio.gather(
            guarded_query_task, transformed_query_task
        )
        
        # 2. Hybrid Retrieval
        retrieved_docs = await self.retriever.retrieve(transformed_query, top_k=50)
        
        # 3. Contextual Re-ranking
        reranked_docs = await self.reranker.rerank(guarded_query, retrieved_docs, user_id, top_k=5)
        
        # 4. Prompt Construction and Generation
        final_prompt = self.generator.construct_prompt(guarded_query, reranked_docs)
        
        # 5. Streaming Generation and Output Guardrails
        token_stream = self.generator.stream_response(final_prompt)
        async for token in guardrails.apply_output_guardrails(token_stream):
            yield token