
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

def load_ga4_robust(filepath):
    print("Loading GA4 with index_col=False...")
    try:
        # index_col=False forces pandas to NOT use the first column as index even if header/data mismatch
        df = pd.read_csv(filepath, skiprows=6, on_bad_lines='skip', index_col=False)
        
        # In case the extra column "Grand total" in row 8 caused a shift anyway?
        # If index_col=False, pandas might ignore the extra data at the END of the row, 
        # or fill the header with Unnamed if data has more cols.
        # Let's inspect.
        
        # The summary row (line 8) starts with empty string. 
        # If 'Landing page' column contains NaN/Empty, drop it.
        if 'Landing page' in df.columns:
            df = df.dropna(subset=['Landing page'])
            # Also drop if it looks like the summary row
            df = df[df['Landing page'].astype(str).str.contains('/', na=False)]
            
        print("GA4 Head Cleaned:")
        print(df.head(3))
        
        df = df.rename(columns={'Landing page': 'Landing_Page'})
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
        'Koszulkowy_Contribution_Profit_7_Days_Attribution_PLN': 'Contribution_Profit',
        'Hook_Rate': 'Hook_Rate',
        'Cost_per_purchase': 'CPA',
        'Link_ad_settings': 'Landing_Page'
    }
    df_meta = df_meta.rename(columns=meta_map)
    for col in ['Spend', 'Contribution_Profit', 'Hook_Rate', 'CPA']:
        if col in df_meta.columns:
            df_meta[col] = pd.to_numeric(df_meta[col], errors='coerce').fillna(0)

    df_meta['Normalized_URL'] = df_meta['Landing_Page'].apply(normalize_url).astype(str)

    # --- LOAD GA4 ---
    df_ga4 = load_ga4_robust(ga4_path)
    if df_ga4.empty:
        print("GA4 Dataframes empty, aborting.")
        return

    # Standardize GA4
    col_map_ga4 = {
        'Total revenue': 'TotalRevenue',
        'Sessions': 'Sessions',
        'ARPU': 'ARPU',
        'Average purchase revenue': 'AvgOrderValue'
    }
    for c in df_ga4.columns:
        for k, v in col_map_ga4.items():
            if k in c:
                df_ga4 = df_ga4.rename(columns={c: v})
    
    for col in ['TotalRevenue', 'ARPU', 'Sessions']:
        if col in df_ga4.columns:
            df_ga4[col] = pd.to_numeric(df_ga4[col], errors='coerce').fillna(0)
            
    df_ga4['Normalized_URL'] = df_ga4['Landing_Page'].astype(str).apply(lambda x: x.strip())

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
    video_keywords = ['video', 'film', 'rolka', 'shorts', 'reel', 'unboxing']
    df_meta['Is_Video_Intent'] = df_meta['Ad_Name'].str.lower().apply(lambda x: any(k in str(x) for k in video_keywords))
    video_ads = df_meta[df_meta['Is_Video_Intent'] & (df_meta['Spend'] > 50)]
    
    if not video_ads.empty:
        suspects = video_ads[video_ads['Hook_Rate'] < 0.10].sort_values('Spend', ascending=False)
        print(f"Found {len(suspects)} video ads with Hook Rate < 10%. Top Suspects:")
        print(suspects[['Ad_Name', 'Spend', 'Hook_Rate']].head(5))

    # --- RECOMMENDATION ---
    candidates = merged[merged['TotalRevenue'] > 500].copy() # Filter noise
    
    print("\n--- TOP 5 PROVEN WINNERS (Meta Profit) ---")
    # Only consider if Meta Spend > 0 (Proof of scale)
    winners = candidates[candidates['Meta_Spend'] > 100].sort_values('Meta_Profit', ascending=False).head(5)
    print(winners[['Landing_Page', 'Meta_Profit', 'Meta_Spend', 'TotalRevenue']])
    
    print("\n--- TOP 5 HIDDEN GEMS (Organic Potential) ---")
    # High Organic, Low Meta Spend
    candidates['Gem_Score'] = candidates['ARPU'] * np.log1p(candidates['TotalRevenue'])
    gems = candidates[candidates['Meta_Spend'] < 100].sort_values('Gem_Score', ascending=False).head(10)
    print(gems[['Landing_Page', 'TotalRevenue', 'ARPU', 'Meta_Spend']])

if __name__ == "__main__":
    analyze_strategy(
        r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\Untitled-report-Jan-1-2026-to-Jan-31-2026.csv",
        r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\download (1).csv"
    )
