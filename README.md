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

- **`Clients/`**: Client-specific data and configuration.
- **`Koszulkowy/`**: Analysis reports and data for the Koszulkowy brand.
- **`Strategy/`**: Strategic analysis scripts and deep-dive tools.
- **`campaigns/`**: Specific marketing pushes and ad sets.
- **`assets/`**: Raw deliverables.
  - `images/`: Static banners.
  - `videos/`: Raw footage and exports.
  - `copy/`: Ad texts and headlines.
- **`Reports/`**: Analysis output and performance reviews.

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
