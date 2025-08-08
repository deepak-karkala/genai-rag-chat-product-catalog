import pandas as pd
from analysis import ab_test_analysis

def create_sample_data(control_users, control_conversions, challenger_users, challenger_conversions):
    """Helper function to create a sample DataFrame for testing."""
    data = {
        'variant_id': ['control'] * control_users + ['challenger'] * challenger_users,
        'converted': [True] * control_conversions + [False] * (control_users - control_conversions) + \
                     [True] * challenger_conversions + [False] * (challenger_users - challenger_conversions)
    }
    return pd.DataFrame(data)

def test_conversion_rate_significant_difference():
    """Test case where there is a clear, statistically significant difference."""
    df = create_sample_data(10000, 500, 10000, 600) # 5% vs 6% conversion
    _, _, p_value = ab_test_analysis.analyze_conversion_rate(df)
    assert p_value is not None
    assert p_value < 0.05

def test_conversion_rate_no_difference():
    """Test case where there is no significant difference."""
    df = create_sample_data(10000, 500, 10000, 505) # 5.0% vs 5.05%
    _, _, p_value = ab_test_analysis.analyze_conversion_rate(df)
    assert p_value is not None
    assert p_value > 0.05