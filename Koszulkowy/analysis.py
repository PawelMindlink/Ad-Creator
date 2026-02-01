
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
    except:
        return None

try:
    # --- LOAD META DATA ---
    print("Loading Meta Data...")
    df_meta = pd.read_csv(meta_file)
    df_meta.columns = [c.strip() for c in df_meta.columns]
    
    if 'Delivery level' in df_meta.columns:
        df_meta = df_meta[df_meta['Delivery level'] == 'ad']
    
    df_meta['product_id'] = df_meta['Link (ad settings)'].apply(extract_product_id)
    
    profit_col = 'Koszulkowy Contribution Profit (7 Days Attribution) (PLN)'
    if profit_col not in df_meta.columns:
        possible = [c for c in df_meta.columns if 'Profit' in c]
        if possible:
            profit_col = possible[0]
    
    for col in ['Amount spent (PLN)', 'Purchases conversion value', profit_col, 'Purchases']:
        if col in df_meta.columns:
            df_meta[col] = pd.to_numeric(df_meta[col], errors='coerce').fillna(0)

    df_meta_products = df_meta.dropna(subset=['product_id'])
    
    meta_agg = df_meta_products.groupby('product_id').agg({
        'Amount spent (PLN)': 'sum',
        'Purchases conversion value': 'sum',
        'Purchases': 'sum',
        profit_col: 'sum',
        'Link (ad settings)': 'first'
    }).reset_index()
    
    meta_agg.rename(columns={
        'Amount spent (PLN)': 'Meta_Spend',
        'Purchases conversion value': 'Meta_Revenue',
        'Purchases': 'Meta_Purchases',
        profit_col: 'Meta_Profit'
    }, inplace=True)

    # --- LOAD GA4 DATA ---
    print("Loading GA4 Data...")
    # Use usecols to avoid jagged line issues
    # Columns based on file inspection: 0:Landing page, 1:ARPU, 2:Avg purchase rev, 3:Total rev, 4:Sessions, 5:Transactions
    df_ga4 = pd.read_csv(ga4_file, skiprows=6, usecols=[0,1,2,3,4,5])
    
    # Rename columns to standard names to be safe
    df_ga4.columns = ['Landing page', 'ARPU', 'Avg_Purchase_Revenue', 'Total revenue', 'Sessions', 'Transactions']
    
    # Drop rows where Landing page is NaN (like Grand Total row if it was parsed weirdly) or empty
    df_ga4 = df_ga4[df_ga4['Landing page'].notna()]
    # Drop grand total if it's the first data row and has empty string/NaN ID logic
    
    df_ga4['product_id'] = df_ga4['Landing page'].apply(extract_product_id)
    
    # Clean numeric columns
    for col in ['Total revenue', 'Sessions', 'Transactions', 'ARPU']:
        df_ga4[col] = pd.to_numeric(df_ga4[col], errors='coerce').fillna(0)

    df_ga4_products = df_ga4.dropna(subset=['product_id'])
    
    ga4_agg = df_ga4_products.groupby('product_id').agg({
        'Total revenue': 'sum',
        'Sessions': 'sum',
        'Transactions': 'sum',
        'ARPU': 'mean', # Average of ARPU across entries? Or recompute. Weighted average is better.
        'Landing page': 'first'
    }).reset_index()
    
    ga4_agg.rename(columns={
        'Total revenue': 'GA4_Revenue',
        'Sessions': 'GA4_Sessions',
        'Transactions': 'GA4_Transactions'
    }, inplace=True)

    # Recompute ARPU to be accurate
    ga4_agg['GA4_ARPU'] = ga4_agg['GA4_Revenue'] / ga4_agg['GA4_Sessions']
    
    # --- MERGE ---
    merged = pd.merge(ga4_agg, meta_agg, on='product_id', how='outer').fillna(0)
    
    # Prefer non-zero Landing page / Link
    merged['URL'] = merged.apply(lambda x: x['Landing page'] if x['Landing page']!=0 else x['Link (ad settings)'], axis=1)
    
    # Filter out 0 value rows that are useless
    merged = merged[(merged['Meta_Spend'] > 0) | (merged['GA4_Revenue'] > 0)]

    # Scoring / Sorting
    
    # 1. High Potential (High Meta Profit)
    print("\n--- TOP BY CONTRIBUTION PROFIT (META) ---")
    top_meta = merged.sort_values(by='Meta_Profit', ascending=False).head(5)
    print(top_meta[['product_id', 'URL', 'Meta_Profit', 'Meta_Spend', 'Meta_Revenue', 'GA4_Revenue', 'GA4_ARPU']].to_string())

    # 2. Organic Gems (High Revenue, Low Paid Spend) - Scale Potential
    print("\n--- TOP ORGANIC GEMS (HIGH GA4 REV, LOW META SPEND < 500) ---")
    organic = merged[(merged['Meta_Spend'] < 500) & (merged['GA4_Revenue'] > 1000)].sort_values(by='GA4_Revenue', ascending=False).head(5)
    print(organic[['product_id', 'URL', 'GA4_Revenue', 'GA4_ARPU', 'Meta_Spend', 'Meta_Profit']].to_string())

    # 3. High Efficiency (High ARPU/RPS with decent volume) - Conversion Potential
    print("\n--- TOP CONVERSION POTENTIAL (HIGH ARPU, SESSIONS > 50) ---")
    efficient = merged[merged['GA4_Sessions'] > 50].sort_values(by='GA4_ARPU', ascending=False).head(5)
    print(efficient[['product_id', 'URL', 'GA4_ARPU', 'GA4_Sessions', 'GA4_Revenue', 'Meta_Spend']].to_string())

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
