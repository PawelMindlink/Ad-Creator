
import pandas as pd
import numpy as np

# Load the dataset
file_path = 'c:/Users/Paweł/Documents/GitHub/Ad Creator/Koszulkowy/Untitled-report-Jan-1-2026-to-Jan-31-2026.csv'
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    exit()

# Columns to analyze
cols_of_interest = {
    'Hook Rate': 'Hook Rate',
    'Hold Rate': 'Hold Rate',
    'CTR (link click-through rate)': 'CTR',
    'CPM (cost per 1,000 impressions)': 'CPM',
    'Purchases rate per link clicks': 'CVR_Link',
    'Purchases rate per landing page views': 'CVR_LP',
    'Koszulkowy Contribution Profit (7 Days Attribution) (PLN)': 'Profit',
    'Amount spent (PLN)': 'Spend'
}

# Clean and Prepare Data
cleaned_data = {}
for original, alias in cols_of_interest.items():
    if original in df.columns:
        # Force numeric, turning '-' or errors into NaN
        cleaned_data[alias] = pd.to_numeric(df[original], errors='coerce')
    else:
        print(f"Warning: Column '{original}' not found.")

df_clean = pd.DataFrame(cleaned_data)

# Filter for meaningful spend (e.g., > 100 PLN) to avoid noise
df_clean = df_clean[df_clean['Spend'] > 100]

print(f"Analyzing {len(df_clean)} ads with Spend > 100 PLN.\n")

# --- Hypothesis 1: Creative Nuance (Hook/Hold vs CTR/Profit) ---
print("--- Hypothesis 1: Creative Nuance ---")
corr_hook_ctr = df_clean['Hook Rate'].corr(df_clean['CTR'])
corr_hold_profit = df_clean['Hold Rate'].corr(df_clean['Profit'])

print(f"Correlation: Hook Rate vs CTR: {corr_hook_ctr:.4f}")
print(f"Correlation: Hold Rate vs Profit: {corr_hold_profit:.4f}")

if corr_hook_ctr > 0.5:
    print(">> Strong link: Better Hooks drive better CTR.")
else:
    print(">> Weak link: Hooks alone don't guarantee Clicks (Need Body/Headline).")

if corr_hold_profit > 0.5:
    print(">> Strong link: Holding attention (User Value) drives Profit.")
else:
    print(">> Weak link: Attention doesn't guarantee Sales (Need Offer alignment).")

# --- Hypothesis 2: Impression Quality (CPM vs CVR) ---
print("\n--- Hypothesis 2: Impression Quality ---")
corr_cpm_cvr = df_clean['CPM'].corr(df_clean['CVR_Link'])

print(f"Correlation: CPM vs CVR (Link): {corr_cpm_cvr:.4f}")

if corr_cpm_cvr > 0.3:
    print(">> Positive: Paying more (High CPM) yields better buyers (High CVR). System is working.")
elif corr_cpm_cvr < -0.3:
    print(">> Negative: High CPM correlates with LOW CVR. Value destruction (Death Zone).")
else:
    print(">> Neutral: Price of traffic is unrelated to quality. Market is inefficient.")


# --- Additional: Total Value Equation Proxies ---
print("\n--- Total Value Equation Diagnostic ---")
# Check if High EAR (CTR * CVR) correlates with Profit
df_clean['EAR_Proxy'] = df_clean['CTR'] * df_clean['CVR_Link']
corr_ear_profit = df_clean['EAR_Proxy'].corr(df_clean['Profit'])
print(f"Correlation: EAR (Proxy) vs Profit: {corr_ear_profit:.4f}")
