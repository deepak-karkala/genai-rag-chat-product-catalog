import requests
import os
import pytest
from collections import Counter

# PRODUCTION_API_ENDPOINT is the URL of the live, production service
API_ENDPOINT = os.environ["PRODUCTION_API_ENDPOINT"]

@pytest.mark.integration
@pytest.mark.production
def test_traffic_splitting_distribution():
    """Validates that the production traffic split is working as configured."""
    responses = []
    num_requests = 1000
    
    # 1. ACTION: Make 1000 requests to the production endpoint
    for _ in range(num_requests):
        try:
            # The inference service should be configured to return a header
            # indicating which version served the request.
            response = requests.post(f"{API_ENDPOINT}/search", json={"query": "test"}, timeout=5)
            if response.status_code == 200 and 'X-Variant-Version' in response.headers:
                responses.append(response.headers['X-Variant-Version'])
        except requests.RequestException:
            # Ignore timeouts or errors for this specific test
            pass

    # 2. COLLECT: Count the responses from each variant
    counts = Counter(responses)
    control_count = counts.get('control', 0)
    challenger_count = counts.get('challenger', 0)
    
    total_responses = control_count + challenger_count
    assert total_responses > 0, "Did not receive any valid responses from the API."

    challenger_percentage = (challenger_count / total_responses) * 100
    
    # 3. ASSERT: Check if the distribution is within tolerance (e.g., 5% +/- 2%)
    expected_challenger_weight = 5.0
    tolerance = 2.0
    
    print(f"Observed challenger traffic: {challenger_percentage:.2f}%")
    assert abs(challenger_percentage - expected_challenger_weight) < tolerance