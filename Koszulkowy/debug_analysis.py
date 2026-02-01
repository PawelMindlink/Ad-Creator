
import pandas as pd
import glob
import os
import re
from urllib.parse import urlparse

# File paths
meta_file = r'c:/Users/Paweł/Documents/GitHub/Ad Creator/Koszulkowy/Untitled-report-Jan-1-2026-to-Jan-31-2026.csv'
ga4_file = r'c:/Users/Paweł/Documents/GitHub/Ad Creator/Koszulkowy/download (1).csv'

def extract_product_id(url):
    if pd.isna(url) or url == '':
        return None
    try:
        url_str = str(url)
        # Handle full URLs vs relative paths
        if 'http' in url_str:
            path = urlparse(url_str).path
        else:
            path = url_str
            
        # Pattern: /12345-something... or 12345-something
        # Look for digits followed by a hyphen at the start of a segment
        match = re.search(r'/(\d+)-', path)
        if match:
            return match.group(1)
        # Sometimes it might just start with the number if no leading slash?
        match = re.search(r'^(\d+)-', path)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        return None

try:
    print("--- DEBUGGING IDS ---")
    
    # --- LOAD META DATA ---
    df_meta = pd.read_csv(meta_file)
    df_meta.columns = [c.strip() for c in df_meta.columns]
    if 'Delivery level' in df_meta.columns:
        df_meta = df_meta[df_meta['Delivery level'] == 'ad']
    
    df_meta['product_id'] = df_meta['Link (ad settings)'].apply(extract_product_id)
    print(f"Meta Rows: {len(df_meta)}")
    print("Sample Meta IDs:")
    print(df_meta[['Link (ad settings)', 'product_id']].head(10).to_string())
    print(f"Meta Unique IDs: {df_meta['product_id'].nunique()}")

    # --- LOAD GA4 DATA ---
    df_ga4 = pd.read_csv(ga4_file, skiprows=6)
    df_ga4 = df_ga4[df_ga4['Landing page'].notna()]
    
    df_ga4['product_id'] = df_ga4['Landing page'].apply(extract_product_id)
    print(f"\nGA4 Rows: {len(df_ga4)}")
    print("Sample GA4 IDs:")
    print(df_ga4[['Landing page', 'product_id']].head(10).to_string())
    print(f"GA4 Unique IDs: {df_ga4['product_id'].nunique()}")
    
    # --- CHECK OVERLAP ---
    meta_ids = set(df_meta['product_id'].dropna().unique())
    ga4_ids = set(df_ga4['product_id'].dropna().unique())
    
    overlap = meta_ids.intersection(ga4_ids)
    print(f"\nOverlapping IDs: {len(overlap)}")
    print(f"Sample Overlap: {list(overlap)[:5]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
