import pytest
import requests
import os

# API_ENDPOINT is the URL of the deployed staging service
API_ENDPOINT = os.environ["STAGING_API_ENDPOINT"]

@pytest.mark.integration
def test_search_endpoint_returns_success():
    """Tests that the deployed API returns a successful response."""
    response = requests.post(
        f"{API_ENDPOINT}/search",
        json={"query": "what are the best hiking boots?"},
        stream=True
    )
    assert response.status_code == 200
    
    # Assert that we get some streamed content back
    content = ""
    for chunk in response.iter_content(chunk_size=None):
        content += chunk.decode('utf-8')
    
    assert len(content) > 0