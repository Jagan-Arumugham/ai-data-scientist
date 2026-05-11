# Data Dictionary — retail_customers.csv

## Dataset Overview
- **File name:** retail_customers.csv
- **Row count:** 5,000
- **Grain:** One row per customer, snapshot as of Q4 2024
- **Snapshot date or time range:** Snapshot date December 31, 2024. Behavioral variables (purchase count, spend, engagement rates) cover the trailing 12 months January 1 to December 31, 2024. Recency (days_since_last_purchase) is calculated as of the snapshot date.
- **Source system(s):** CRM for demographics and loyalty data. E-commerce and POS systems for transaction data. Email platform for engagement metrics. Mobile app analytics for app behavior.
- **Date last refreshed:** January 10, 2025

---

## Column Definitions

### Target and Outcome Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| lapse_flag | Whether the customer has lapsed — defined as no purchase in the last 90 days | Binary derived from days_since_last_purchase: 1 if > 90 days, 0 otherwise | Binary 0 or 1 | This is the target variable. Do not use days_since_last_purchase alongside this in driver modeling — they are directly collinear. |
| days_since_last_purchase | Number of days since the customer's most recent purchase as of snapshot date | Calculated from last transaction date to snapshot date | Integer, days | Ranges 1 to 180 in this dataset. Use in EDA and profiling only — exclude from driver analysis feature set to prevent leakage into lapse_flag prediction. |

---

### Purchase Behavior Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| purchase_count_12m | Total number of transactions made in the trailing 12 months | Count of distinct transaction records | Integer, count | Minimum value is 1 — all customers in this dataset made at least one purchase in the year. Zero-purchase customers were excluded at data extraction. |
| avg_order_value | Average dollar value per transaction in the trailing 12 months | total_spend_12m / purchase_count_12m | USD, rounded to 2 decimal places | Will be correlated with total_spend_12m — treat as the more interpretable variable alongside purchase_count_12m |
| total_spend_12m | Total dollars spent in the trailing 12 months | Sum of all transaction amounts | USD, rounded to 2 decimal places | Highly correlated with purchase_count_12m and avg_order_value combined. Also the basis for loyalty_tier — expect collinearity. |
| returns_count_12m | Number of items or orders returned in the trailing 12 months | Count of return transactions | Integer, count | Value of 0 is common and valid — many customers have no returns |
| return_rate | Proportion of purchases that were returned | returns_count_12m / purchase_count_12m | Decimal 0 to 1 | Interpret carefully — high return rate can indicate either high engagement (buy a lot, return some) or dissatisfaction. Cross-reference with purchase_count before concluding. |

---

### Product and Category Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| preferred_category | The product category with the highest purchase count for this customer in the trailing 12 months | Derived from transaction data — most frequent category | Categorical: Apparel, Electronics, Home & Garden, Beauty, Sports, Food & Beverage | Reflects trailing 12 months only — may not reflect the customer's long-term category preference if they recently shifted |
| category_count | Number of distinct product categories purchased from in the trailing 12 months | Count of distinct category codes in transaction history | Integer 1 to 6 | A value of 1 means the customer bought from only one category — potential indicator of narrow engagement and higher lapse risk |

---

### Loyalty and Relationship Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| loyalty_tier | Customer loyalty tier based on total spend in the trailing 12 months | Bronze: under $200, Silver: $200-$799, Gold: $800-$1,999, Platinum: $2,000 and above | Categorical: Bronze, Silver, Gold, Platinum | Derived from total_spend_12m — will be correlated. Use loyalty_tier as the more interpretable variable in profiling. Platinum tier is small (~115 customers) — flag for small sample size in segment-level analysis. |
| tenure_months | Number of months since the customer's first purchase with this retailer | Calculated from first transaction date to snapshot date | Integer, months | Ranges 1 to 72 months in this dataset. Customers with very short tenure (under 3 months) may have different lapse dynamics than established customers — flag if tenure shows a non-linear relationship with lapse. |
| preferred_channel | The channel through which the customer makes most of their purchases | Derived from transaction channel flags — most frequent channel | Categorical: Online, In-Store, Omnichannel | Reflects trailing 12 months only. Omnichannel customers purchase across both online and in-store channels. |

---

### Demographic Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| age | Customer age at snapshot date | Calculated from date of birth on file | Integer, years | Ranges 18 to 78 in this dataset. No values below 18 — age-gating applied at data extraction. |
| gender | Customer self-identified gender | CRM — provided at registration | Categorical: Male, Female, Other | Small Other category (~3%) — may need to be collapsed with a larger group or excluded from gender-based sub-analyses due to sample size. |
| region | Geographic region of the customer's primary address | CRM — derived from zip code | Categorical: Northeast, Southeast, Midwest, West, Southwest | Regional distribution is approximately proportional to US population. No nulls. |

---

### Digital Engagement Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| email_open_rate | Proportion of marketing emails opened by the customer in the trailing 12 months | Email platform: opens / emails sent | Decimal 0 to 1 | NULL means the customer has opted out of email marketing entirely — not a missing value. Treat as a distinct behavioral category. Do not impute. ~7.5% of customers are email opt-outs. |
| email_click_rate | Proportion of marketing emails where the customer clicked a link | Email platform: clicks / emails sent | Decimal 0 to 1 | NULL for the same customers as email_open_rate — opt-out status applies to both. email_click_rate will always be less than or equal to email_open_rate for any given customer. |
| app_sessions_30d | Number of mobile app sessions in the trailing 30 days | Mobile app analytics | Integer, count | NULL means the customer has never downloaded the app. Treat as zero engagement — do not impute with mean. ~12% of customers have no app. |
| days_since_app_login | Number of days since the customer's most recent app login as of snapshot date | Mobile app analytics | Integer, days | NULL for same customers as app_sessions_30d — no app download. For active app users, higher values indicate disengagement. |
| promo_response_rate | Proportion of promotional offers the customer responded to (clicked or redeemed) in the trailing 12 months | CRM promotional system | Decimal 0 to 1 | NULL means the customer is not enrolled in the promotional program — not missing data. ~15% of customers are not enrolled. Treat as a separate behavioral category. |

---

### Operational Identifiers

| Column Name | What It Identifies | Should It Be Excluded? |
|---|---|---|
| customer_id | Unique customer identifier | Yes — identifier only, no analytical value |

---

## Null Value Conventions

| Column Name | Null Meaning | Treatment |
|---|---|---|
| email_open_rate | Customer has opted out of email marketing | Create a binary flag: email_optout = 1. Do not impute. |
| email_click_rate | Customer has opted out of email marketing | Same as email_open_rate — always null together |
| app_sessions_30d | Customer has never downloaded the app | Create a binary flag: no_app = 1. Treat metric as zero for engagement scoring. |
| days_since_app_login | Customer has never downloaded the app | Same as app_sessions_30d — always null together |
| promo_response_rate | Customer is not enrolled in promotional program | Create a binary flag: promo_not_enrolled = 1. Do not impute. |

---

## Coded Values and Lookups

| Column Name | Code | Meaning |
|---|---|---|
| loyalty_tier | Bronze | Total spend under $200 in trailing 12 months |
| loyalty_tier | Silver | Total spend $200 to $799 |
| loyalty_tier | Gold | Total spend $800 to $1,999 |
| loyalty_tier | Platinum | Total spend $2,000 and above |
| lapse_flag | 0 | Active customer — purchased within last 90 days |
| lapse_flag | 1 | Lapsed customer — no purchase in last 90 days |

---

## Known Data Quality Issues

1. Platinum tier contains only approximately 115 customers — sub-group analyses on Platinum customers may have insufficient sample size for reliable statistical conclusions. Flag any Platinum-specific finding with a sample size caveat.
2. The Other gender category contains approximately 150 customers — too small for independent segment analysis. Consider collapsing into a combined group or excluding from gender-based breakdowns.
3. return_rate will be zero for all customers with zero returns — this is structurally correct and not a data error. The zero-return group is the majority.

---

## Known Analytical Gotchas

1. days_since_last_purchase directly determines lapse_flag — using both in the same model is data leakage. Use lapse_flag as the target variable in driver analysis and exclude days_since_last_purchase from the feature set entirely.
2. total_spend_12m, purchase_count_12m, avg_order_value, and loyalty_tier are all intercorrelated — they measure different facets of the same underlying behavior (buying more or less). Expect high correlations between them in EDA. Select the most interpretable pair for modeling — recommended: purchase_count_12m and avg_order_value.
3. Null patterns in engagement columns are structural and informative — the fact that a customer opted out of email is itself a behavioral signal that should be captured as a binary flag rather than imputed or excluded.
4. Short-tenure customers (under 6 months) may have naturally lower purchase counts simply because they have had less time to buy — not necessarily because they are disengaged. Consider whether to control for tenure in the driver analysis or to analyze short-tenure customers separately.
