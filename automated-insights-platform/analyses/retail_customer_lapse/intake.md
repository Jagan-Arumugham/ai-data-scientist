# Analysis Intake — Retail Customer Lapse

## Business Question
Which customers are at risk of lapsing — defined as making no purchase in the last 90 days — and what behavioral, engagement, and demographic factors drive that behavior? We want to understand what distinguishes lapsed customers from active ones, identify the highest-risk segments, and surface actionable drivers that a retention or re-engagement program could target.

## Dataset
- CSV file: `data/retail_customers.csv`
- Data dictionary: `data/retail_customers_data_dictionary.md`

## Analysis Scope
- Population: All customers with at least one purchase in the trailing 12 months. Customers with zero purchase activity in 12 months are already fully lapsed and should be excluded from the core analysis — they are a separate retention problem.
- Time period: Behavioral variables (purchase count, spend, engagement) cover the trailing 12 months from snapshot date. Recency (days_since_last_purchase) is as of snapshot date.
- Level of granularity: One row per customer.

## Domain Conventions
- lapse_flag = 1 means the customer has not made a purchase in the last 90 days. lapse_flag = 0 means they have purchased within the last 90 days. This is the target variable.
- days_since_last_purchase is the primary recency measure. It directly determines lapse_flag — do not use both as independent features in the driver analysis. Use lapse_flag as the target and exclude days_since_last_purchase from the feature set to avoid data leakage.
- Null values in email_open_rate and email_click_rate mean the customer has opted out of email marketing — not that the data is missing. Treat as a separate behavioral category: email opt-out.
- Null values in app_sessions_30d and days_since_app_login mean the customer has never downloaded the app. Treat as zero engagement, not as missing data.
- Null values in promo_response_rate mean the customer is not enrolled in the promotional program. Treat as a separate category, not as missing data.

## Known Hypotheses Going In
1. Low purchase frequency and high recency are the strongest predictors of lapse — customers who were already buying infrequently are most at risk.
2. Digital disengagement (low email engagement, low app usage) precedes lapse — these are leading indicators that a customer is drifting before they stop buying entirely.
3. Single-category buyers are at higher lapse risk than multi-category buyers — customers with breadth across categories have more reasons to return.
4. Bronze loyalty tier customers lapse at a higher rate than Silver, Gold, and Platinum — lower investment in the relationship means less friction to leave.
5. Shorter tenure customers may lapse at a higher rate — they have not yet formed a strong habit of purchasing from this retailer.

## Known Risk Factors or Confounders
- days_since_last_purchase directly defines lapse_flag — exclude it from driver analysis feature set to prevent data leakage. It can be used in EDA and profiling to characterize segments but not as a model input.
- total_spend_12m and purchase_count_12m multiplied by avg_order_value are highly collinear — expect a strong correlation between them. Retain purchase_count_12m and avg_order_value as the more interpretable pair.
- loyalty_tier is derived from total_spend_12m — these will be correlated. Treat loyalty_tier as the more interpretable variable for segmentation and profiling.
- High return rates could indicate either highly engaged customers (who buy a lot and return some) or dissatisfied customers (who return because products disappoint). Interpret with care — check whether return_rate differs meaningfully between lapsed and active customers before drawing conclusions.

## Nodes to Run
- [x] EDA
- [x] Segmentation
- [x] Profiling
- [x] Driver Analysis
- [x] Insight Synthesis

Nodes to skip: none

## Stakeholder Context
Primary audience is the Head of Customer Retention and the CRM team. They are comfortable with segment-level findings and want clear targeting criteria they can operationalize in a re-engagement campaign. They want to know: who should we target, what message or offer is most likely to work for each segment, and how many customers are in each risk tier. They are not interested in model mechanics — they want business-language findings with customer counts.

## Prior Analyses to Be Aware Of
None — this is the first lapse analysis run on this dataset. Findings will become the baseline for future quarterly comparisons.

## Output Required
A structured findings document with an executive summary, key findings, segment profiles with customer counts, prioritized recommendations with targeting logic, and open questions. The recommendations should be specific enough to brief a CRM team on campaign design.
