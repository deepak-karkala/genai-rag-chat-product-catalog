import asyncio
import json
import logging
import os
import random
from typing import List, Dict, Any

import pandas as pd
from aiohttp import ClientError
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import BedrockChat

# --- Configuration ---
# In a real project, this would come from a config file or environment variables.
CONFIG = {
    "PRODUCT_CATALOG_PATH": "data/raw/product_catalog.csv",
    "SEED_QUERIES_PATH": "data/raw/seed_queries.txt",
    "OUTPUT_PATH": "data/processed/golden_evaluation_dataset.jsonl",
    "LLM_MODEL_ID": "anthropic.claude-3-opus-20240229-v1:0",
    "MAX_QUERIES_PER_CHUNK": 7,
    "NUM_SEED_EXAMPLES": 5,
    "MAX_CONCURRENT_REQUESTS": 10,  # Important to avoid rate limiting
}

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Core Functions ---

def load_seed_queries(filepath: str) -> List[str]:
    """Loads the seed query list from a text file."""
    try:
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"Seed queries file not found at: {filepath}")
        return []

def load_product_documents(filepath: str) -> pd.DataFrame:
    """Loads product catalog data from a CSV."""
    try:
        df = pd.read_csv(filepath)
        # Ensure required columns exist
        if 'product_id' not in df.columns or 'description' not in df.columns:
            raise ValueError("CSV must contain 'product_id' and 'description' columns.")
        return df.dropna(subset=['product_id', 'description'])
    except FileNotFoundError:
        logger.error(f"Product catalog file not found at: {filepath}")
        return pd.DataFrame()

def chunk_document(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Splits a document's text into smaller chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return splitter.split_text(text)

async def generate_queries_for_chunk(
    llm: BedrockChat,
    chunk_text: str,
    seed_queries: List[str]
) -> List[str]:
    """Uses an LLM to generate a list of queries for a given text chunk."""
    
    # Randomly sample seed queries to provide varied examples in the prompt
    examples = "\n".join(f"- \"{q}\"" for q in random.sample(seed_queries, CONFIG["NUM_SEED_EXAMPLES"]))
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a data scientist creating a high-quality evaluation dataset for an e-commerce semantic search engine. "
         "Your task is to generate realistic user search queries that can be answered by the provided text snippet from a product description. "
         "The queries must be diverse, reflecting different user intents (e.g., questions, feature requests, comparisons, use-cases). "
         "The answer to each query you generate MUST be present in the provided context. Do NOT generate questions requiring outside knowledge. "
         "Output a JSON object with a single key 'queries' containing a list of strings."),
        ("human", 
         "**CONTEXT (Product Information Snippet):**\n---\n{context}\n---\n\n"
         "**EXAMPLES of QUERY STYLES:**\n{examples}\n\n"
         f"Please generate {CONFIG['MAX_QUERIES_PER_CHUNK']} realistic and diverse user queries based on the context above.")
    ])
    
    parser = JsonOutputParser()
    chain = prompt_template | llm | parser

    try:
        response = await chain.ainvoke({"context": chunk_text, "examples": examples})
        if "queries" in response and isinstance(response["queries"], list):
            return response["queries"]
        else:
            logger.warning(f"LLM returned malformed JSON, missing 'queries' list. Response: {response}")
            return []
    except (ClientError, json.JSONDecodeError, Exception) as e:
        logger.error(f"Error generating queries for chunk: {e}")
        return []

async def process_document(
    semaphore: asyncio.Semaphore,
    llm: BedrockChat,
    product: pd.Series,
    seed_queries: List[str],
    output_file
):
    """Chunks a document, generates queries for each chunk, and writes to the output file."""
    async with semaphore:
        try:
            product_id = product['product_id']
            description = product['description']
            
            chunks = chunk_document(description)
            logger.info(f"Processing product {product_id}: split into {len(chunks)} chunks.")
            
            tasks = []
            for i, chunk in enumerate(chunks):
                tasks.append(generate_queries_for_chunk(llm, chunk, seed_queries))
            
            generated_queries_per_chunk = await asyncio.gather(*tasks)

            for i, queries in enumerate(generated_queries_per_chunk):
                for query in queries:
                    record = {
                        "query": query,
                        "relevant_product_id": str(product_id),
                        "source_chunk_id": i
                    }
                    output_file.write(json.dumps(record) + "\n")
        
        except Exception as e:
            logger.error(f"Failed to process product {product.get('product_id', 'N/A')}: {e}")

async def main():
    """Main orchestration function."""
    logger.info("Starting synthetic golden dataset generation.")
    
    seed_queries = load_seed_queries(CONFIG["SEED_QUERIES_PATH"])
    product_df = load_product_documents(CONFIG["PRODUCT_CATALOG_PATH"])

    if not seed_queries or product_df.empty:
        logger.error("Cannot proceed without seed queries and product data. Exiting.")
        return

    # Initialize the LLM
    llm = BedrockChat(
        model_id=CONFIG["LLM_MODEL_ID"],
        model_kwargs={"temperature": 0.7, "max_tokens": 2048}
    )

    # Use a semaphore to limit concurrent API calls
    semaphore = asyncio.Semaphore(CONFIG["MAX_CONCURRENT_REQUESTS"])
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(CONFIG["OUTPUT_PATH"]), exist_ok=True)

    with open(CONFIG["OUTPUT_PATH"], 'w') as output_file:
        tasks = []
        for _, product in product_df.iterrows():
            tasks.append(process_document(semaphore, llm, product, seed_queries, output_file))
        
        # Process all documents concurrently
        await asyncio.gather(*tasks)

    logger.info(f"Dataset generation complete. Output saved to {CONFIG['OUTPUT_PATH']}")

if __name__ == "__main__":
    # Ensure AWS credentials and LangSmith env variables are set before running
    # e.g., export LANGCHAIN_TRACING_V2=true; export LANGCHAIN_API_KEY=...
    asyncio.run(main())