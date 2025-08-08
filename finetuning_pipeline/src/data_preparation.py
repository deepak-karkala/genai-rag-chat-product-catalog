import pandas as pd
import logging
from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch # and other clients
from sklearn.model_selection import train_test_split
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This would be initialized with proper credentials
opensearch_client = OpenSearch(...) 
production_embedding_model = SentenceTransformer('intfloat/multilingual-e5-large')

def load_interaction_data(log_bucket: str, date_prefix: str) -> pd.DataFrame:
    """Loads and merges user interaction logs from S3."""
    # In a real scenario, this would read multiple Parquet/JSON files from S3,
    # potentially using AWS Data Wrangler (awswrangler).
    logger.info(f"Loading interaction data from s3://{log_bucket}/{date_prefix}")
    # Placeholder for data loading logic
    sample_data = {
        'session_id': ['s1', 's1', 's2', 's2', 's2'],
        'query': ['queryA', 'queryA', 'queryB', 'queryB', 'queryB'],
        'retrieved_product_id': ['prod1', 'prod2', 'prod3', 'prod4', 'prod5'],
        'clicked': [False, True, False, False, True],
        'purchased': [False, True, False, False, False]
    }
    return pd.DataFrame(sample_data)

def get_product_text(product_id: str) -> str:
    """Fetches the text content for a given product ID."""
    # This would query a database or another S3 location
    return f"Full text description for {product_id}." # Placeholder

def perform_hard_negative_mining(query: str, positive_id: str) -> str:
    """Finds a hard negative for a given query and positive example."""
    query_embedding = production_embedding_model.encode(query)
    
    # Retrieve top 5 results from the current production index
    # This simulates what the user would have seen
    response = opensearch_client.search(...) # Search with query_embedding
    
    retrieved_ids = [hit['_source']['product_id'] for hit in response['hits']['hits']]
    
    # Find the first retrieved ID that is NOT the one the user purchased
    for an_id in retrieved_ids:
        if an_id != positive_id:
            logger.info(f"Found hard negative '{an_id}' for query '{query}'")
            return get_product_text(an_id)
            
    return None # Could happen if user buys the top result

def create_triplets(df: pd.DataFrame) -> List[Tuple[str, str, str]]:
    """Constructs (anchor, positive, negative) triplets from interaction data."""
    triplets = []
    successful_interactions = df[df['purchased'] == True]
    
    for _, row in successful_interactions.iterrows():
        anchor = row['query']
        positive_text = get_product_text(row['retrieved_product_id'])
        negative_text = perform_hard_negative_mining(anchor, row['retrieved_product_id'])
        
        if anchor and positive_text and negative_text:
            triplets.append((anchor, positive_text, negative_text))
            
    logger.info(f"Successfully created {len(triplets)} training triplets.")
    return triplets

def main():
    # This script would be run by the Airflow task
    interaction_df = load_interaction_data("rag-log-archive-prod", "2025/08/")
    triplets = create_triplets(interaction_df)
    
    # Convert to a DataFrame and save to S3
    triplets_df = pd.DataFrame(triplets, columns=['anchor', 'positive', 'negative'])
    train_df, val_df = train_test_split(triplets_df, test_size=0.1)
    
    # Save to S3 in a versioned folder (e.g., using the run date)
    # train_df.to_csv("s3://rag-finetuning-data/train_YYYY-MM-DD.csv")
    # val_df.to_csv("s3://rag-finetuning-data/val_YYYY-MM-DD.csv")