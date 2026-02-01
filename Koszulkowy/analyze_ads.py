
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 1000)

def load_and_analyze(filepath):
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    # Normalize headers
    df.columns = [c.strip().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '') for c in df.columns]
    
    # Rename some critical columns for easier access if they exist
    # Based on the file view, columns like "Ad name", "Amount spent (PLN)", "Purchases", "Cost per purchase", "Koszulkowy Contribution Profit (7 Days Attribution) (PLN)", "Hook Rate", "Hold Rate", "CTR (link click-through rate)"
    
    column_map = {
        'Ad_name': 'Ad_Name',
        'Amount_spent_PLN': 'Spend',
        'Purchases': 'Purchases',
        'Cost_per_purchase': 'CPA',
        'Koszulkowy_Contribution_Profit_7_Days_Attribution_PLN': 'Contribution_Profit',
        'Hook_Rate': 'Hook_Rate',
        'Hold_Rate': 'Hold_Rate',
        'CTR_link_click-through_rate': 'CTR',
        'Body_ad_settings': 'Ad_Body',
        'Link_ad_settings': 'Landing_Page'
    }
    
    # Check which columns are actually present
    print("Columns present:", df.columns.tolist())
    
    df = df.rename(columns=column_map)
    
    # Filter for relevant columns
    cols_to_keep = ['Ad_Name', 'Spend', 'Purchases', 'CPA', 'Contribution_Profit', 'Hook_Rate', 'Hold_Rate', 'CTR', 'Ad_Body']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    df = df[existing_cols]

    # Clean numeric columns (handle currency symbols, commas etc if necessary, though CSV usually has raw numbers)
    # The view showed raw numbers, but let's be safe.
    # The view showed "2974.63" as float, so it should be fine. But Contribution Profit had " zł" in the markdown report? 
    # Wait, the CSV view showed "2551.46112195" under profit, so it seems numeric. 
    # BUT "Hook Rate" had "7.48E-6" or empty.
    
    numeric_cols = ['Spend', 'Purchases', 'CPA', 'Contribution_Profit', 'Hook_Rate', 'Hold_Rate', 'CTR']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filter for significant spend (> 20 PLN) to avoid noise
    df_active = df[df['Spend'] > 20].copy()
    
    print(f"\nAnalyzed {len(df_active)} ads with Spend > 20 PLN (out of {len(df)} total rows).")
    
    # 1. Identify Winners vs Losers based on Contribution Profit
    df_active = df_active.sort_values(by='Contribution_Profit', ascending=False)
    
    top_performers = df_active.head(10)
    bottom_performers = df_active.tail(10)
    
    print("\n--- TOP 10 PERFORMERS (By Contribution Profit) ---")
    print(top_performers[['Ad_Name', 'Spend', 'Contribution_Profit', 'CPA', 'Hook_Rate', 'CTR']].to_string(index=False))
    
    print("\n--- BOTTOM 10 PERFORMERS (By Contribution Profit) ---")
    print(bottom_performers[['Ad_Name', 'Spend', 'Contribution_Profit', 'CPA', 'Hook_Rate', 'CTR']].to_string(index=False))

    # 2. Analyze Correlations
    print("\n--- CORRELATION ANALYSIS (Spend weighted) ---")
    corr_cols = ['Spend', 'Contribution_Profit', 'CPA', 'Hook_Rate', 'Hold_Rate', 'CTR']
    # Filter only columns that exist
    corr_cols = [c for c in corr_cols if c in df_active.columns]
    
    correlation = df_active[corr_cols].corr()['Contribution_Profit'].sort_values(ascending=False)
    print(correlation)

    # 3. Categorize Ads (Simple heuristics based on name)
    def categorize_ad(name):
        name = str(name).lower()
        if 'dpa' in name: return 'DPA'
        if 'karuzela' in name: return 'Carousel'
        if 'video' in name or 'film' in name or 'rolka' in name: return 'Video'
        if 'baner' in name: return 'Banner'
        return 'Other/Static'

    df_active['Format'] = df_active['Ad_Name'].apply(categorize_ad)
    
    print("\n--- PERFORMANCE BY FORMAT ---")
    format_stats = df_active.groupby('Format').agg({
        'Ad_Name': 'count',
        'Spend': 'sum',
        'Contribution_Profit': 'sum',
        'Purchases': 'sum',
        'CPA': 'mean',
        'Hook_Rate': 'mean',
        'CTR': 'mean'
    }).sort_values(by='Contribution_Profit', ascending=False)
    
    # Recalculate weighed CPA
    format_stats['Real_CPA'] = format_stats['Spend'] / format_stats['Purchases']
    print(format_stats)

    # 4. Deep Dive into "Winners" traits
    # Calculate avg Hook Rate for profitable vs unprofitable ads
    profitable_ads = df_active[df_active['Contribution_Profit'] > 0]
    unprofitable_ads = df_active[df_active['Contribution_Profit'] <= 0]
    
    print("\n--- METRICS: PROFITABLE VS UNPROFITABLE ---")
    print(f"Profitable Ads Count: {len(profitable_ads)}")
    print(f"Unprofitable Ads Count: {len(unprofitable_ads)}")
    print(f"Avg Hook Rate (Profitable): {profitable_ads['Hook_Rate'].mean():.4f}")
    print(f"Avg Hook Rate (Unprofitable): {unprofitable_ads['Hook_Rate'].mean():.4f}")
    print(f"Avg CTR (Profitable): {profitable_ads['CTR'].mean():.4f}")
    print(f"Avg CTR (Unprofitable): {unprofitable_ads['CTR'].mean():.4f}")
    print(f"Avg Release Date (Profitable): N/A (needs date parsing)") # Placeholder
    
    # 5. Text Analysis (Mini)
    # Check for common words in winning ad bodies
    pass 

if __name__ == "__main__":
    load_and_analyze(r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\Untitled-report-Jan-1-2026-to-Jan-31-2026.csv")
