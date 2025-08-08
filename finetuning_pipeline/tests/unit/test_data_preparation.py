import pandas as pd
from unittest.mock import patch
from src import data_preparation

@patch('src.data_preparation.production_embedding_model')
@patch('src.data_preparation.opensearch_client')
def test_hard_negative_mining_logic(mock_os_client, mock_model):
    """Tests that the hard negative mining correctly selects a non-positive document."""
    # ARRANGE
    test_query = "test query"
    positive_product_id = "prod-positive"
    
    # Mock the OpenSearch response
    mock_os_client.search.return_value = {
        'hits': {'hits': [
            {'_source': {'product_id': 'prod-hard-negative'}},
            {'_source': {'product_id': 'prod-positive'}},
            {'_source': {'product_id': 'prod-other'}}
        ]}
    }
    
    # ACT
    hard_negative = data_preparation.perform_hard_negative_mining(test_query, positive_product_id)
    
    # ASSERT
    # It should have picked the first result that was not the positive one.
    assert "prod-hard-negative" in hard_negative