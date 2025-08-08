import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, ttest_ind
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_conversion_rate(df: pd.DataFrame, control_name='control', challenger_name='challenger'):
    """Performs a Chi-squared test for conversion rates."""
    contingency_table = pd.crosstab(df['variant_id'], df['converted'])
    
    if control_name not in contingency_table.index or challenger_name not in contingency_table.index:
        logging.warning("Control or challenger variant not found in the data.")
        return None, None, None

    chi2, p_value, _, _ = chi2_contingency(contingency_table)
    
    control_conv_rate = contingency_table.loc[control_name, True] / contingency_table.loc[control_name].sum()
    challenger_conv_rate = contingency_table.loc[challenger_name, True] / contingency_table.loc[challenger_name].sum()
    
    logging.info(f"Control Conversion Rate: {control_conv_rate:.4f}")
    logging.info(f"Challenger Conversion Rate: {challenger_conv_rate:.4f}")
    logging.info(f"Chi-squared p-value: {p_value:.4f}")
    
    return control_conv_rate, challenger_conv_rate, p_value

def analyze_aov(df: pd.DataFrame, control_name='control', challenger_name='challenger'):
    """Performs an independent T-test for Average Order Value."""
    control_aov = df[df['variant_id'] == control_name]['order_value'].dropna()
    challenger_aov = df[df['variant_id'] == challenger_name]['order_value'].dropna()

    if control_aov.empty or challenger_aov.empty:
        logging.warning("No order data for one or both variants.")
        return None, None, None

    _, p_value = ttest_ind(control_aov, challenger_aov, equal_var=False) # Welch's T-test
    
    logging.info(f"Control AOV: ${control_aov.mean():.2f}")
    logging.info(f"Challenger AOV: ${challenger_aov.mean():.2f}")
    logging.info(f"T-test p-value: {p_value:.4f}")
    
    return control_aov.mean(), challenger_aov.mean(), p_value

def generate_report(data_path: str, alpha: float = 0.05):
    """Loads data and generates a full A/B test report."""
    logging.info(f"Loading experiment data from {data_path}...")
    # In a real scenario, this would connect to a data warehouse like Redshift or BigQuery.
    # For this example, we'll use a CSV.
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logging.error(f"Data file not found at {data_path}")
        return

    logging.info("\n--- Conversion Rate Analysis ---")
    _, _, conv_p_value = analyze_conversion_rate(df)
    
    if conv_p_value is not None:
        if conv_p_value < alpha:
            logging.info("Result: Statistically significant difference in conversion rates found.")
        else:
            logging.info("Result: No statistically significant difference in conversion rates.")

    logging.info("\n--- Average Order Value (AOV) Analysis ---")
    _, _, aov_p_value = analyze_aov(df)
    if aov_p_value is not None:
        if aov_p_value < alpha:
            logging.info("Result: Statistically significant difference in AOV found.")
        else:
            logging.info("Result: No statistically significant difference in AOV.")

    # --- Final Recommendation Logic ---
    # (This would be more sophisticated in a real business context)
    logging.info("\n--- Recommendation ---")
    if conv_p_value is not None and conv_p_value < alpha:
        logging.info("Promote Challenger: Strong evidence of impact on conversion.")
    else:
        logging.info("Decision: Continue experiment or conclude with no significant finding.")

if __name__ == "__main__":
    # Example usage:
    # python ab_test_analysis.py data/experiment_results.csv
    import sys
    if len(sys.argv) > 1:
        generate_report(sys.argv[1])
    else:
        logging.error("Please provide the path to the experiment data CSV.")