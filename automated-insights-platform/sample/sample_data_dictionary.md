# Data Dictionary — Sample (tenured_clients.csv)

## Dataset Overview
- **File name:** tenured_clients.csv
- **Row count:** approximately 47,000
- **Grain:** One row per client, snapshot as of Q4 2024
- **Snapshot date or time range:** Snapshot date December 31, 2024. Flow variables (inflow, outflow) cover trailing 12 months January 1 to December 31, 2024.
- **Source system(s):** CRM system for demographic and relationship data. Digital analytics platform for engagement data. Trading system for trading behavior. Core banking for flow and balance data.
- **Date last refreshed:** January 15, 2025

---

## Column Definitions

### Target and Outcome Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| outflow_amount | Total dollars moved out of all accounts in trailing 12 months | Sum of all debit transactions flagged as client-initiated withdrawals | USD, positive values only | Null means zero — client had no outflows. Do not treat as missing. |
| inflow_amount | Total dollars moved into all accounts in trailing 12 months | Sum of all credit transactions flagged as client-initiated deposits | USD, positive values only | Null means zero. Do not treat as missing. |
| net_flow | Net flow = inflow_amount minus outflow_amount | Calculated field | USD, can be negative | Negative values indicate net outflower. Zero is possible. |

---

### Financial and Balance Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| total_aum | Total assets under management across all accounts at snapshot date | Sum of all account balances at snapshot date | USD | May differ from AUM used in other systems due to valuation methodology differences |
| cash_pct | Percentage of total AUM held in cash and cash equivalents | cash_balance / total_aum | Percentage 0 to 100 | Should sum with equity_pct and fixed_income_pct to approximately 100. Flag rows where sum deviates by more than 5 points. |
| equity_pct | Percentage of total AUM held in equities | equity_balance / total_aum | Percentage 0 to 100 | See cash_pct note |
| fixed_income_pct | Percentage of total AUM held in fixed income | fixed_income_balance / total_aum | Percentage 0 to 100 | See cash_pct note |
| wealth_tier | Client wealth tier based on total AUM | 1 = under $100k, 2 = $100k to $500k, 3 = $500k to $1M, 4 = over $1M | Integer 1 to 4 | Tier is assigned at snapshot date — may not reflect peak AUM if client has already partially withdrawn |

---

### Behavioral and Engagement Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| login_frequency | Number of digital logins in trailing 90 days, web and mobile combined | Digital analytics platform | Integer, count | Null means zero logins — client has not used digital channels. Treat as zero, not missing. |
| mobile_sessions | Number of mobile app sessions in trailing 90 days | Digital analytics platform | Integer, count | Null means zero. |
| days_since_last_login | Days since most recent digital login as of snapshot date | Calculated from last_login_date | Integer, days | Very high values (500+) indicate clients who may have never used digital channels |
| trade_count | Number of trades executed in trailing 12 months across all accounts | Trading system | Integer, count | Null means zero trades. |
| days_since_last_trade | Days since most recent trade as of snapshot date | Calculated from last_trade_date | Integer, days | Null means never traded — do not treat as missing |
| options_flag | Whether client has traded options in trailing 12 months | Trading system | Binary 0 or 1 | Only tracked from July 2023 onward. Clients onboarded before this date may show false negatives. |

---

### Demographic Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| age | Client age at snapshot date | Calculated from date of birth | Integer, years | Values below 18 are data errors — flag and exclude. Values above 95 are rare but plausible. |
| tenure_months | Months since account open date as of snapshot date | Calculated from account_open_date to snapshot date | Integer, months | Clients acquired via 2022 acquisition may have tenure reset to acquisition date rather than original open date — if tenure analysis looks anomalous this is the likely cause |

---

### Relationship Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| product_count | Number of distinct product types held across all accounts | CRM | Integer, count | Minimum value should be 1 — flag any zero values as potential data error |
| has_checking | Whether client holds a checking account with the bank | CRM | Binary 0 or 1 | Reflects current status at snapshot date only |
| has_savings | Whether client holds a savings account with the bank | CRM | Binary 0 or 1 | Reflects current status at snapshot date only |
| has_mortgage | Whether client holds a mortgage with the bank | CRM | Binary 0 or 1 | Reflects current status at snapshot date only |
| risk_score | Self-reported risk tolerance score | CRM — client self-reported at onboarding or last profile update | Integer 1 to 10, higher = more risk tolerant | Self-reported and potentially stale. Check risk_score_updated_date — scores older than 18 months should be treated with caution as a current behavioral signal |
| risk_score_updated_date | Date risk score was last updated | CRM | Date | Use to assess staleness of risk_score |

---

### Operational Identifiers

| Column Name | What It Identifies | Should It Be Excluded? |
|---|---|---|
| client_id | Unique client identifier | Yes — identifier only, no analytical value |
| account_id | Primary account identifier | Yes — identifier only |
| branch_code | Branch associated with the client relationship | Yes — operational code, no analytical value |
| rm_id | Relationship manager identifier | Yes — operational code |
| rep_code | Representative code from trading system | Yes — operational code |

---

## Null Value Conventions

| Column Name | Null Meaning | Treatment |
|---|---|---|
| outflow_amount | Client had no outflows in the period | Treat as zero |
| inflow_amount | Client had no inflows in the period | Treat as zero |
| login_frequency | Client had no digital logins in trailing 90 days | Treat as zero |
| mobile_sessions | Client had no mobile sessions in trailing 90 days | Treat as zero |
| trade_count | Client made no trades in trailing 12 months | Treat as zero |
| days_since_last_trade | Client has never traded | Flag as non-trader — do not impute a numeric value |
| days_since_last_login | Client has never used digital channels | Flag as never-digital — treat days_since as very high (e.g. 9999) for ranking purposes |

---

## Coded Values and Lookups

| Column Name | Code | Meaning |
|---|---|---|
| wealth_tier | 1 | Total AUM under $100,000 |
| wealth_tier | 2 | Total AUM $100,000 to $499,999 |
| wealth_tier | 3 | Total AUM $500,000 to $999,999 |
| wealth_tier | 4 | Total AUM $1,000,000 or above |

---

## Known Data Quality Issues

1. Asset mix columns (cash_pct, equity_pct, fixed_income_pct) do not always sum to 100% — a small number of rows have rounding errors or unclassified assets. Flag rows where the sum deviates from 100% by more than 5 percentage points.
2. options_flag was not tracked before July 2023. Clients with account open dates before that date may show a false zero on this field — it does not mean they have not traded options.
3. A small number of clients (~200) show total_aum of zero despite having had inflow activity — likely an account closure during the period. Flag these for exclusion from AUM-based analysis.

---

## Known Analytical Gotchas

1. The 65 to 70 age band often shows elevated outflow that reflects Required Minimum Distribution (RMD) withdrawals — a regulatory requirement, not behavioral dissatisfaction. Do not interpret this as a pure behavioral signal without flagging the regulatory alternative explanation.
2. December and January flow data reflects year-end tax-motivated moves and RMD distributions. If the snapshot or analysis period covers these months, outflow figures may be seasonally elevated.
3. Very high absolute outflow amounts in the top wealth tier (tier 4) may reflect normal rebalancing behavior in large portfolios rather than client dissatisfaction. Consider analyzing flow as a percentage of AUM rather than in absolute dollars for cross-wealth-tier comparisons.
4. Clients acquired via the 2022 acquisition have tenure_months calculated from the acquisition date, not their original account open date. Their "true" tenure with the firm is longer than the column indicates. If the analysis shows anomalous tenure patterns, this population should be investigated separately.
