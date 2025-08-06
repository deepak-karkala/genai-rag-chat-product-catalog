import logging
from typing import List
from langchain_community.embeddings import BedrockEmbeddings

logger = logging.getLogger(__name__)

def generate_text_embeddings(chunks: List[str]) -> List[List[float]]:
    """Generates embeddings for a list of text chunks."""
    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v2:0",
    )
    logger.info(f"Generating text embeddings for {len(chunks)} chunks.")
    return embeddings.embed_documents(chunks)

def generate_image_embedding(image_bytes: bytes) -> List[float]:
    """Generates an embedding for a single image."""
    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-image-v1",
    )
    logger.info(f"Generating image embedding for image of size {len(image_bytes)} bytes.")
    # The actual implementation would involve base64 encoding the image
    return embeddings.embed_query("placeholder for image bytes") # Placeholder