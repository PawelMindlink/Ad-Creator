# Ad Creator

> **Business Goal**: Increase ad performance and profit by systematically analyzing Meta Ads and GA4 data to identify and promote high-potential products.

## Definition (Business Logic)

**Objective**:

- **Primary KPI**: Contribution Profit (Margin - Ad Spend).
- **Secondary KPI**: Identification of "Organic Gems" (High organic sales, low ad spend) for scaling.

**Target Audience**:

- E-commerce managers and media buyers looking for data-driven ad concepts.
- Creative teams needing performance data to inform ad angles.

**Hypotheses**:

1. Products with high organic performance ("Hidden Gems") will scale profitably with paid support.
2. Aligning ad creative with specific "Jobs to be Done" (JTBD) of the product increases CTR and Conversion Rate.

## Structure (Assets & Code)

This project is organized as follows:

- **`campaigns/`**: Top-level directory for all marketing pushes.
  - `[YYYY-MM]_[CampaignName]/`: dedicated folder for each campaign (e.g., `2026-02_Round2_Concepts`).
    - `[PROD_ID]_[ShortName]/`: Creative Unit for a specific product.
      - `1x1/`: Square assets.
      - `9x16/`: Vertical assets.
      - `ad_kit.md`: **Single Source of Truth** for Copy, Links, and Strategy.
- **`Clients/`**: Client-specific data and configuration.
- **`Koszulkowy/`**: Analysis reports and brand data.
- **`Strategy/`**: Strategic analysis scripts.
- **assets/**: Shared assets (logos, images, copy).
  - `images/`: Static banners.
  - `videos/`: Raw footage.
  - `copy/`: Ad texts.
  - `references/`: Inspiration and templates (e.g., PDFs, Swipe Files).

## Asset Naming Convention

All creative files must follow this strict format:

`[PROD_ID]_[ShortName]_[Angle]_[Ratio]_[Version].[ext]`

Example:
`15735_GeraltBluza_UrbanWitcher_1x1_v1.png`

- **PROD_ID**: Product ID from e-commerce platform.
- **ShortName**: Readable product slug.
- **Angle**: The creative concept (e.g., `SocialProof`, `Urban`).
- **Ratio**: `1x1`, `9x16`, `4x5`.
- **Version**: `v1`, `v2`, etc.

## Operation (How to use)

### 1. Analysis

Run deep dive analysis scripts from `Strategy/` to identify top products.
Example: `python Strategy/analyze_koszulkowy_deep_dive.py`

### 2. Campaign Creation

Uses the insights from analysis to generate ad concepts in `campaigns/`.

### 3. Reporting

Check `Koszulkowy/analysis_report.md` for the latest "Top Products" and "Organic Gems".

---
*Maintained by: Marketing Engineering Team*
