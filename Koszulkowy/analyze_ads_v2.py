
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
    
    df = df.rename(columns=column_map)
    
    # Filter for relevant columns
    cols_to_keep = ['Ad_Name', 'Spend', 'Purchases', 'CPA', 'Contribution_Profit', 'Hook_Rate', 'Hold_Rate', 'CTR', 'Ad_Body']
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    df = df[existing_cols]

    numeric_cols = ['Spend', 'Purchases', 'CPA', 'Contribution_Profit', 'Hook_Rate', 'Hold_Rate', 'CTR']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Filter for significant spend (> 50 PLN) for meaningful stats
    df_active = df[df['Spend'] > 50].copy()
    
    # Categorize Ads
    def categorize_ad(name):
        name = str(name).lower()
        if 'dpa' in name: return 'DPA'
        if 'karuzela' in name: return 'Carousel'
        if 'video' in name or 'film' in name or 'rolka' in name: return 'Video'
        if 'baner' in name: return 'Banner'
        return 'Static_Image'

    df_active['Format'] = df_active['Ad_Name'].apply(categorize_ad)
    
    # 1. Segmented Correlation Analysis
    print("\n--- SEGMENTED CORRELATION (Profit Drivers) ---")
    
    # For Video: Hook Rate vs Profit
    video_ads = df_active[df_active['Format'] == 'Video']
    if not video_ads.empty:
        print(f"\n[VIDEO ADS] (n={len(video_ads)}) Correlations with Contribution Profit:")
        print(video_ads[['Spend', 'Hook_Rate', 'Hold_Rate', 'CTR', 'CPA']].corrwith(video_ads['Contribution_Profit']).sort_values(ascending=False))
    
    # For Static: CTR vs Profit
    static_ads = df_active[df_active['Format'].isin(['Static_Image', 'Banner'])]
    if not static_ads.empty:
        print(f"\n[STATIC ADS] (n={len(static_ads)}) Correlations with Contribution Profit:")
        print(static_ads[['Spend', 'CTR', 'CPA']].corrwith(static_ads['Contribution_Profit']).sort_values(ascending=False))

    # 2. Keyword/Niche Analysis
    print("\n--- NICHE PERFORMANCE ANALYSIS ---")
    
    niches = {
        'Ranczo': ['ranczo', 'wilkowyje', 'mamrot', 'solejuk'],
        'Farmers/Tractor': ['traktor', 'rolnik', 'dziadek', 'krowy'],
        'Gaming/Kids': ['roblox', 'minecraft', '67', 'six seven', 'game'],
        'Professions': ['nauczyciel', 'strażak', 'elektryk', 'budowlaniec', 'szef', 'biur'],
        'Occasions': ['babcia', 'dziadek', 'walentynki', 'święta', 'urodziny']
    }
    
    results = []
    
    for niche, keywords in niches.items():
        # Create a mask for ads matching any keyword in the niche
        pattern = '|'.join(keywords)
        mask = df_active['Ad_Name'].str.contains(pattern, case=False, na=False) | df_active['Ad_Body'].str.contains(pattern, case=False, na=False)
        
        niche_df = df_active[mask]
        
        if not niche_df.empty:
            stats = {
                'Niche': niche,
                'Count': len(niche_df),
                'Total_Spend': niche_df['Spend'].sum(),
                'Total_Profit': niche_df['Contribution_Profit'].sum(),
                'Avg_ROAS': niche_df['Contribution_Profit'].sum() / niche_df['Spend'].sum(), # ROI actually
                'Avg_CPA': niche_df['Spend'].sum() / niche_df['Purchases'].sum() if niche_df['Purchases'].sum() > 0 else 0,
                'Best_Ad': niche_df.sort_values('Contribution_Profit', ascending=False).iloc[0]['Ad_Name']
            }
            results.append(stats)
            
    niche_stats = pd.DataFrame(results).sort_values('Total_Profit', ascending=False)
    print(niche_stats[['Niche', 'Count', 'Total_Spend', 'Total_Profit', 'Avg_CPA', 'Best_Ad']].to_string(index=False))

    # 3. Creative Angle Check (Round 2 matches)
    print("\n--- ROUND 2 CONCEPTS PERFORMANCE (Keyword Match) ---")
    round2_keywords = {
        'Social Proof / Opinions': ['opinia', 'klient', 'zadowolona', 'gwiazdki', '4.8/5'],
        'Fear/Pain (Paszport/Stolica)': ['stolica', 'paszport', 'koniec świata'],
        'Magical/Surreal (Portal/Świeca)': ['portal', 'magia', '1670', 'sarmac'],
        'Urgency/Delivery': ['24h', 'dostawa', 'jutro', 'szybka'],
        'Identity/Ego (Prezes/Szef)': ['szef', 'prezes', 'zarząd', 'biuro', 'rolnik'], # Overlap with professions but specific angle
    }
    
    r2_results = []
    for angle, keywords in round2_keywords.items():
        pattern = '|'.join(keywords)
        mask = df_active['Ad_Name'].str.contains(pattern, case=False, na=False) | df_active['Ad_Body'].str.contains(pattern, case=False, na=False)
        angle_df = df_active[mask]
        
        if not angle_df.empty:
            r2_results.append({
                'Angle': angle,
                'Profit': angle_df['Contribution_Profit'].sum(),
                'Spend': angle_df['Spend'].sum(),
                'Ads': len(angle_df)
            })
            
    if r2_results:
        print(pd.DataFrame(r2_results).sort_values('Profit', ascending=False))
    else:
        print("No direct matches found for Round 2 specific keywords in high-spend ads.")

if __name__ == "__main__":
    load_and_analyze(r"c:\Users\Paweł\Documents\GitHub\Ad Creator\Koszulkowy\Untitled-report-Jan-1-2026-to-Jan-31-2026.csv")
