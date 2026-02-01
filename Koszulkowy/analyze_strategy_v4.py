
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 1000)

def normalize_url(url):
    if pd.isna(url): return ""
    url = str(url).strip()
    # Remove protocol and domain if present
    if 'koszulkowy.pl' in url:
        return '/' + url.split('koszulkowy.pl/')[-1]
    # Remove trailing/leading spaces
    return url

def load_ga4_robust(filepath):
    # GA4 export often has a summary row at the top with weird formatting or extra columns
    # We'll skip the first 6 lines of metadata
    # And then we'll try to read it.
    print("Loading GA4 with robust logic...")
    try:
        # Read header only first
        header_df = pd.read_csv(filepath, skiprows=6, nrows=0)
        expected_cols = header_df.columns.tolist()
        print(f"Expected GA4 cols: {expected_cols}")
        
        # Read data, handling bad lines
        df = pd.read_csv(filepath, skiprows=6, on_bad_lines='skip')
        
        # Check if the first row is the "Grand total" summary row which often shifts columns
        # In the file view, line 8 started with an empty comma and ended with "Grand total"
        # If 'Landing page' column is missing or empty in the first row, drop it
        first_col = df.columns[0] # Should be 'Landing page'
        
        # Filter: Keep only rows where 'Landing page' starts with '/' or contains text, not empty/float
        # Drop rows where Landing page is NaN
        df = df.dropna(subset=[first_col])
        
        # Further filter: Eliminate rows that look like summary stats (e.g. if Landing page is just numbers or empty string)
        # In the bug, "Landing page" became "7.045118" (ARPU value). 
        # This implies misaligned read.
        
        # If we see misaligned data, we might need to reload with 'index_col=False' or similar.
        # But let's look at the data we got.
        print("First 5 rows raw:")
        print(df.head(5))
        
        # Heuristic: If 'Landing page' column contains floats, it's wrong.
        # Check type of first column
        if pd.api.types.is_float_dtype(df[first_col]):
            print("WARNING: First column detected as FLOAT. Shift likely occurred.")
            # If shift occurred, it's likely because the summary row (line 8) had an empty first field and pandas treated it as index?
            # Or maybe the summary row had 7 tokens and header 6...
            
            # Let's try reloading excluding the summary row (row 8 in file = row 0 in df?)
            # Actually, easiest fix if we know the header names:
            # Re-read forcing names
            df = pd.read_csv(filepath, skiprows=7, names=expected_cols, on_bad_lines='skip')
            # Note: skiprows=7 skips the header too! So we provide names.
            print("Reloaded skipping line 8 (summary)...")
            print(df.head())
            
        # Clean up
        df = df.rename(columns={df.columns[0]: 'Landing_Page'})
        return df
        
    except Exception as e:
        print(f"Error loading GA4: {e}")
        return pd.DataFrame()

def analyze_strategy(meta_path, ga4_path):
    # --- LOAD META ---
    try:
        df_meta = pd.read_csv(meta_path)
    except Exception as e:
        print(f"Meta Load Error: {e}")
        return

    df_meta.columns = [c.strip().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '') for c in df_meta.columns]
    
    meta_map = {
        'Ad_name': 'Ad_Name',
        'Amount_spent_PLN': 'Spend',
        'Purchases': 'Purchases',
        'Cost_per_purchase': 'CPA',
        'Koszulkowy_Contribution_Profit_7_Days_Attribution_PLN': 'Contribution_Profit',
        'Hook_Rate': 'Hook_Rate',
        'Link_ad_settings': 'Landing_Page'
    }
    df_meta = df_meta.rename(columns=meta_map)
    for col in ['Spend', 'Purchases', 'Contribution_Profit', 'Hook_Rate']:
        if col in df_meta.columns:
            df_meta[col] = pd.to_numeric(df_meta[col], errors='coerce').fillna(0)

    df_meta['Normalized_URL'] = df_meta['Landing_Page'].apply(normalize_url).astype(str)

    # --- LOAD GA4 ---
    df_ga4 = load_ga4_robust(ga4_path)
    if df_ga4.empty:
        print("GA4 Dataframes empty, aborting.")
        return

    # Standardize GA4
    # Expected columns: Landing_Page, ARPU, Average purchase revenue, Total revenue, Sessions, Transactions
    # Map them safely
    col_map_ga4 = {
        'Total revenue': 'TotalRevenue',
        'Sessions': 'Sessions',
        'ARPU': 'ARPU'
    }
    # Find matching columns
    for c in df_ga4.columns:
        for k, v in col_map_ga4.items():
            if k in c: # loose match
                df_ga4 = df_ga4.rename(columns={c: v})
    
    for col in ['TotalRevenue', 'ARPU', 'Sessions']:
        if col in df_ga4.columns:
            df_ga4[col] = pd.to_numeric(df_ga4[col], errors='coerce').fillna(0)
            
    df_ga4['Normalized_URL'] = df_ga4['Landing_Page'].astype(str)

    # --- MERGE ---
    meta_by_url = df_meta.groupby('Normalized_URL').agg({
        'Spend': 'sum',
        'Contribution_Profit': 'sum',
        'Ad_Name': 'count'
    }).reset_index().rename(columns={'Spend': 'Meta_Spend', 'Contribution_Profit': 'Meta_Profit'})

    # Inner join to see overlap, left join for gems
    merged = pd.merge(df_ga4, meta_by_url, on='Normalized_URL', how='left')
    merged['Meta_Spend'] = merged['Meta_Spend'].fillna(0)
    merged['Meta_Profit'] = merged['Meta_Profit'].fillna(0)

    # --- VIDEO CHECK ---
    print("\n--- VIDEO INTENT CHECK ---")
    video_keywords = ['video', 'film', 'rolka', 'shorts', 'reel']
    df_meta['Is_Video_Intent'] = df_meta['Ad_Name'].str.lower().apply(lambda x: any(k in str(x) for k in video_keywords))
    video_ads = df_meta[df_meta['Is_Video_Intent'] & (df_meta['Spend'] > 50)]
    
    if not video_ads.empty:
        suspects = video_ads[video_ads['Hook_Rate'] < 0.10].sort_values('Spend', ascending=False)
        print(f"Found {len(suspects)} video ads with Hook Rate < 10%. Top 5:")
        print(suspects[['Ad_Name', 'Spend', 'Hook_Rate']].head(5))

    # --- RECOMMENDATION ---
    # Filter: Valid Pages (Revenue > 500)
    candidates = merged[merged['TotalRevenue'] > 500].copy()
    
    # Logic:
    # 1. Proven Winners: High Meta Profit
    # 2. Hidden Gems: High Organic Revenue + High ARPU + Low Meta Spend (< 100)
    
    print("\n--- TOP 5 PROVEN WINNERS (Meta Profit) ---")
    winners = candidates.sort_values('Meta_Profit', ascending=False).head(5)
    print(winners[['Landing_Page', 'Meta_Profit', 'Meta_Spend', 'TotalRevenue']])
    
    print("\n--- TOP 5 HIDDEN GEMS (Organic Potential) ---")
    # Score = ARPU * log(TotalRevenue)
    candidates['Gem_Score'] = candidates['ARPU'] * np.log1p(candidates['TotalRevenue'])
    gems = candidates[candidates['Meta_Spend'] < 100].sort_values('Gem_Score', ascending=False).head(5)
    print(gems[['Landing_Page', 'Gem_Score', 'TotalRevenue', 'ARPU', 'Meta_Spend']])

if __name__ == "__main__":
    analyze_strategy(
        r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\Untitled-report-Jan-1-2026-to-Jan-31-2026.csv",
        r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\download (1).csv"
    )
