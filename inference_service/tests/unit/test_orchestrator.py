import pytest
from unittest.mock import AsyncMock

from src.orchestrator import RAGOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_full_flow(mocker):
    """Tests the full orchestration flow with mocked dependencies."""
    # ARRANGE: Mock all external clients and their async methods
    mock_retriever = AsyncMock()
    mock_reranker = AsyncMock()
    mock_generator = AsyncMock()
    mock_transformer = AsyncMock()

    mock_retriever.retrieve.return_value = [{"page_content": "doc1"}]
    mock_reranker.rerank.return_value = [{"page_content": "reranked_doc1"}]
    mock_generator.stream_response.return_value = (token for token in ["This", " is", " a", " test."]) # Async generator mock
    mock_transformer.transform_query.return_value = "transformed query"
    
    mocker.patch('src.guardrails.apply_input_guardrails', return_value="safe query")
    mocker.patch('src.guardrails.apply_output_guardrails', side_effect=lambda x: x) # Pass-through mock

    orchestrator_instance = RAGOrchestrator(
        settings=mocker.Mock(),
        retriever_client=mock_retriever,
        reranker_client=mock_reranker,
        generator_client=mock_generator,
        transformer_client=mock_transformer
    )

    # ACT: Run the orchestrator
    query = "test query"
    result_stream = orchestrator_instance.stream_rag_response(query, "user123")
    result = "".join([token async for token in result_stream])

    # ASSERT: Verify that all components were called correctly
    mock_transformer.transform_query.assert_awaited_once_with(query)
    mock_retriever.retrieve.assert_awaited_once_with("transformed query", top_k=50)
    mock_reranker.rerank.assert_awaited_once()
    mock_generator.construct_prompt.assert_called_once()
    mock_generator.stream_response.assert_called_once()
    assert result == "This is a test."