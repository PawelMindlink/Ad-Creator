
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 1000)

def normalize_url(url):
    if pd.isna(url): return ""
    url = str(url).strip()
    if 'koszulkowy.pl' in url:
        return '/' + url.split('koszulkowy.pl/')[-1]
    return url

def analyze_strategy(meta_path, ga4_path):
    print(f"Loading Meta: {meta_path}")
    print(f"Loading GA4: {ga4_path}")
    
    # --- LOAD META ---
    try:
        df_meta = pd.read_csv(meta_path)
    except Exception as e:
        print(f"Error loading Meta CSV: {e}")
        return

    # Normalize Meta headers
    df_meta.columns = [c.strip().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '') for c in df_meta.columns]
    
    # Rename Meta columns
    meta_map = {
        'Ad_name': 'Ad_Name',
        'Amount_spent_PLN': 'Spend',
        'Purchases': 'Purchases',
        'Cost_per_purchase': 'CPA',
        'Koszulkowy_Contribution_Profit_7_Days_Attribution_PLN': 'Contribution_Profit',
        'Hook_Rate': 'Hook_Rate',
        'Hold_Rate': 'Hold_Rate',
        'CTR_link_click-through_rate': 'CTR',
        'Link_ad_settings': 'Landing_Page'
    }
    df_meta = df_meta.rename(columns=meta_map)
    
    # Numeric conversion
    for col in ['Spend', 'Purchases', 'CPA', 'Contribution_Profit', 'Hook_Rate', 'CTR']:
        if col in df_meta.columns:
            df_meta[col] = pd.to_numeric(df_meta[col], errors='coerce').fillna(0)

    # Normalize Meta URLs
    df_meta['Normalized_URL'] = df_meta['Landing_Page'].apply(normalize_url).astype(str)

    # --- LOAD GA4 ---
    try:
        df_ga4 = pd.read_csv(ga4_path, skiprows=6) # Skip header rows
    except Exception as e:
        print(f"Error loading GA4 CSV: {e}")
        return

    # Rename GA4 columns (standardize)
    df_ga4.columns = [c.strip() for c in df_ga4.columns]
    
    # Numeric conversion GA4
    for col in ['ARPU', 'Total revenue', 'Sessions', 'Transactions']:
        if col in df_ga4.columns:
            df_ga4[col] = pd.to_numeric(df_ga4[col], errors='coerce').fillna(0)

    # Normalize GA4 URLs
    # Fix: Ensure GA4 Normalized_URL is strictly string to match Meta
    df_ga4['Normalized_URL'] = df_ga4['Landing page'].astype(str)

    # --- MERGE DATA ---
    # Aggregate Meta by URL first
    meta_by_url = df_meta.groupby('Normalized_URL').agg({
        'Spend': 'sum',
        'Contribution_Profit': 'sum',
        'Purchases': 'sum',
        'Ad_Name': 'count' # Number of ads pointing here
    }).reset_index()
    
    meta_by_url = meta_by_url.rename(columns={'Spend': 'Meta_Spend', 'Contribution_Profit': 'Meta_Profit', 'Purchases': 'Meta_Purchases', 'Ad_Name': 'Ad_Count'})

    # Join
    merged = pd.merge(df_ga4, meta_by_url, on='Normalized_URL', how='left')
    merged['Meta_Spend'] = merged['Meta_Spend'].fillna(0)
    merged['Meta_Profit'] = merged['Meta_Profit'].fillna(0)
    
    # --- ANALYSIS 1: VIDEO VALIDATION ---
    print("\n--- VIDEO CLASSIFICATION CHECK ---")
    video_keywords = ['video', 'film', 'rolka', 'shorts', 'reel']
    df_meta['Is_Video_Intent'] = df_meta['Ad_Name'].str.lower().apply(lambda x: any(k in str(x) for k in video_keywords))
    
    video_ads = df_meta[df_meta['Is_Video_Intent'] & (df_meta['Spend'] > 50)]
    print(f"Detected {len(video_ads)} high-spend ads with 'Video' intent in name.")
    if not video_ads.empty:
        # Check specific "Suspects" (High spend, low hook rate)
        # Assuming Hook Rate is a ratio 0.0-1.0
        suspects = video_ads[video_ads['Hook_Rate'] < 0.10].sort_values('Spend', ascending=False)
        print(f"\nPotential 'Fake Videos' (Slideshows?) count: {len(suspects)}")
        if not suspects.empty:
            print("\nTop 5 Suspects (Low Hook Rate but Video Name):")
            print(suspects[['Ad_Name', 'Spend', 'Hook_Rate']].head(5))
            
    # --- ANALYSIS 2: LANDING PAGE RECOMMENDATION ---
    print("\n--- TOP LANDING PAGES CANDIDATES ---")
    
    # Score 2: Potential (GA4 High ARPU + High Volume + Low Meta Spend)
    # We want High ARPU (Conversion power) & High Revenue (Volume proof), but Low Ad Spend (Untapped)
    merged['Potential_Score'] = (merged['ARPU'] * np.log1p(merged['Total revenue'])) / (np.log1p(merged['Meta_Spend']) + 1)
    
    # Filter valid candidates (e.g. > 1000 PLN revenue total to ignore noise)
    candidates = merged[merged['Total revenue'] > 1000].copy()
    
    print("\nTOP PROVEN (Already making profit on Meta):")
    print(candidates.sort_values('Meta_Profit', ascending=False)[['Landing page', 'Meta_Profit', 'Meta_Spend', 'ARPU']].head(5))
    
    print("\nTOP HIDDEN GEMS (High Organic, Low Ad Spend):")
    print(candidates.sort_values('Potential_Score', ascending=False)[['Landing page', 'Total revenue', 'ARPU', 'Meta_Spend', 'Potential_Score']].head(7))

if __name__ == "__main__":
    analyze_strategy(
        r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\Untitled-report-Jan-1-2026-to-Jan-31-2026.csv",
        r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\download (1).csv"
    )
