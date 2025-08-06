import pytest
from src import text_processor

def test_chunk_text_splits_correctly():
    """Ensures text is split into multiple chunks."""
    long_text = "This is a sentence. " * 200
    chunks = text_processor.chunk_text(long_text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    # Check if overlap is working
    assert chunks[1].startswith(chunks[0][-50:])

def test_get_image_caption_mocked(mocker):
    """Tests the image captioning function with a mocked Bedrock client."""
    # We mock the Bedrock client to avoid making a real API call
    mock_bedrock = mocker.patch('boto3.client')
    # conceptually, you would mock the invoke method's return value
    
    caption = text_processor.get_image_caption(b"fake_image_bytes")
    assert isinstance(caption, str)
    assert len(caption) > 0