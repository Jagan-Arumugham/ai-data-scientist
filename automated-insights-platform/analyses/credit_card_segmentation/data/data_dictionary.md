# Data Dictionary — cc_general.csv

## Dataset Overview
- **File name:** cc_general.csv
- **Row count:** ~8,950
- **Grain:** One row per credit card account (customer-level)
- **Snapshot date or time range:** 6-month behavioral snapshot. All variables summarize account activity over the same 6-month observation window. No specific calendar dates are provided in the dataset.
- **Source system(s):** Credit card transaction system and account management platform. Variables reflect a combination of transaction-level aggregations (purchases, cash advances, payments) and account-level attributes (credit limit, tenure).
- **Date last refreshed:** Not specified in source documentation.

---

## Column Definitions

---

### Target and Outcome Variables

No pre-defined target variable. This is an unsupervised segmentation problem — the segment assignments produced by clustering will become the outcome variable for profiling.

---

### Financial Balance Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| BALANCE | Current account balance — the amount owed on the card at the time of the snapshot | Account ledger balance at snapshot date | USD (approximate) | This is a point-in-time snapshot, not an average over the 6 months. A customer who paid down a large balance just before snapshot will appear low-balance despite being a high-usage account. Interpret alongside BALANCE_FREQUENCY for a more complete picture. |
| CREDIT_LIMIT | The maximum credit line approved for this account | Set at account origination or last credit review | USD | Contains ~1% null values — accounts where credit limit data was not available at extraction. Do not impute with mean. Flag and treat separately — see Null Value Conventions. |
| PAYMENTS | Total dollar amount of payments made by the customer over the 6-month window | Sum of all payment transactions | USD | Includes both minimum payments and full payments. On its own, a high PAYMENTS value does not distinguish a responsible payer from a high-spender paying down large charges. Use alongside PRC_FULL_PAYMENT and MINIMUM_PAYMENTS to interpret repayment behavior. |
| MINIMUM_PAYMENTS | Total dollar amount of minimum payments made over the 6-month window | Sum of statement minimum payment amounts | USD | Contains ~3.5% null values — structural missingness, not behavioral. See Null Value Conventions. A customer with high MINIMUM_PAYMENTS relative to PAYMENTS is carrying revolving debt and paying the minimum — a materially different risk profile from one paying in full. |

---

### Purchase Behavior Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| PURCHASES | Total dollar amount of all purchases made from the account over 6 months | Sum of all purchase transaction amounts | USD | PURCHASES = ONEOFF_PURCHASES + INSTALLMENTS_PURCHASES by construction. Including all three in the same clustering model will double-weight purchase behavior. Retain the two components and exclude PURCHASES, or retain PURCHASES and exclude the components. Decide at EDA. |
| ONEOFF_PURCHASES | Total dollar amount of purchases made in a single transaction (not split into installments) | Sum of non-installment purchase transaction amounts | USD | Customers with high ONEOFF_PURCHASES relative to INSTALLMENTS_PURCHASES prefer large, immediate purchases — potentially higher-income or lower credit-stress customers. Zero is a valid and common value. |
| INSTALLMENTS_PURCHASES | Total dollar amount of purchases made via installment plans over 6 months | Sum of installment purchase transaction amounts | USD | Zero is valid and common — many customers do not use installment purchasing. A high value relative to ONEOFF_PURCHASES suggests the customer relies on installments, potentially indicating budget management behavior or preference for deferred payment. |
| PURCHASES_TRX | Number of individual purchase transactions made over 6 months | Count of distinct purchase transaction records | Integer count | Captures transaction frequency independently of dollar volume. A customer with many low-value purchases (high PURCHASES_TRX, low avg per transaction) has a different behavioral profile from one with few high-value purchases. |

---

### Cash Advance Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| CASH_ADVANCE | Total dollar amount of cash advances taken over 6 months | Sum of cash advance transaction amounts | USD | Zero is valid and common — many customers never take cash advances. A non-zero value is behaviorally significant. High cash advance usage typically indicates the customer is using the credit card as a short-term loan rather than a purchase instrument. Associated with higher credit risk. |
| CASH_ADVANCE_TRX | Number of cash advance transactions made over 6 months | Count of distinct cash advance transactions | Integer count | Should be analyzed together with CASH_ADVANCE. A customer with many small cash advance transactions (high CASH_ADVANCE_TRX, low per-transaction value) has a different behavioral profile from one taking occasional large advances. |
| CASH_ADVANCE_FREQUENCY | How frequently cash advances are taken — normalized score over the 6-month window | Derived frequency score | 0 to 1 scale (0 = never, 1 = every statement cycle) | Bounded variable — will have mass at exactly 0 for customers who never take cash advances. Check what proportion of accounts have CASH_ADVANCE_FREQUENCY = 0 before clustering; if it is above 50%, this variable may behave more like a binary flag than a continuous feature. |

---

### Behavioral Frequency Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| BALANCE_FREQUENCY | How frequently the account balance is updated over the 6-month window | Derived frequency score based on statement cycles with balance activity | 0 to 1 scale (0 = never updated, 1 = updated every cycle) | A score near 1 means the customer consistently carries a balance. A score near 0 means the account is rarely active. Useful for distinguishing dormant accounts from active revolvers. |
| PURCHASES_FREQUENCY | How frequently purchases are made over the 6-month window | Derived frequency score | 0 to 1 scale (0 = no purchases, 1 = purchases every cycle) | Will be highly correlated with PURCHASES_TRX — they measure the same underlying behavior from different angles (frequency vs. count). Expect high correlation in EDA. Retain the one that adds more discriminating power in clustering. |
| ONEOFF_PURCHASES_FREQUENCY | How frequently one-off (non-installment) purchases are made | Derived frequency score | 0 to 1 scale | Will be correlated with ONEOFF_PURCHASES. Zero mass likely to be high — many customers never make one-off large purchases. |
| PURCHASES_INSTALLMENTS_FREQUENCY | How frequently installment purchases are made | Derived frequency score | 0 to 1 scale | Will be correlated with INSTALLMENTS_PURCHASES. Zero mass likely to be high — many customers never use installment purchasing. |

---

### Repayment Behavior Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| PRC_FULL_PAYMENT | Proportion of statement cycles in which the customer paid the full balance | Count of full-payment cycles / total cycles | 0 to 1 scale (0 = never paid in full, 1 = always paid in full) | This is the cleanest indicator of repayment discipline. A value of 1.0 indicates a transactor — someone who never carries a revolving balance and generates no interest income. A value near 0 indicates a revolver. Distribution likely to be bimodal — mass at 0 (never pays in full) and at 1 (always pays in full), with relatively few customers in between. |

---

### Relationship Variables

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| TENURE | Number of months the customer has held the credit card account | Calculated from account open date to snapshot date | Integer, months | Ranges 6 to 12 in this dataset — limited variance. All customers have been active for at least 6 months. Short tenure range may limit TENURE's discriminating power as a segmentation variable. Consider using it as a control rather than a segmentation dimension. |

---

### Operational Identifiers

| Column Name | What It Identifies | Should It Be Excluded? |
|---|---|---|
| CUST_ID | Unique customer account identifier | Yes — identifier only, no analytical value. Exclude before clustering. Retain as a reference key for labeling segment assignments after clustering. |

---

## Null Value Conventions

| Column Name | Null Meaning | Treatment |
|---|---|---|
| CREDIT_LIMIT | Credit limit data was not available at extraction — structural missing, not behavioral | Flag the affected rows. Decision at EDA: if fewer than 2% of rows are affected, impute with median and note it. If more, present the analyst with the option to exclude those rows entirely. Do not impute with mean — CREDIT_LIMIT is likely right-skewed. |
| MINIMUM_PAYMENTS | Structural missing — minimum payment data not available for these accounts, likely due to account type or data extraction gap | Same treatment as CREDIT_LIMIT — flag, decide at EDA whether to impute with median or exclude rows. Do not interpret null MINIMUM_PAYMENTS as "no minimum payment required." |

---

## Coded Values and Lookups

| Column Name | Code | Meaning |
|---|---|---|
| PURCHASES_FREQUENCY | 0 | No purchases in the 6-month window |
| PURCHASES_FREQUENCY | 1 | Purchases made in every statement cycle |
| PRC_FULL_PAYMENT | 0 | Never paid the full statement balance |
| PRC_FULL_PAYMENT | 1 | Paid the full statement balance in every cycle |
| CASH_ADVANCE_FREQUENCY | 0 | No cash advances taken |
| CASH_ADVANCE_FREQUENCY | 1 | Cash advance taken in every statement cycle |
| BALANCE_FREQUENCY | 0 | Balance never updated — effectively dormant |
| BALANCE_FREQUENCY | 1 | Balance updated every statement cycle |

---

## Known Data Quality Issues

1. **CREDIT_LIMIT nulls (~1% of rows):** Credit limit data is missing for a small number of accounts. The cause is not documented. Treat as structural missingness — do not infer from other columns. Decision required at EDA on whether to impute (median) or exclude.
2. **MINIMUM_PAYMENTS nulls (~3.5% of rows):** Similar structural missingness. These are not the same accounts as the CREDIT_LIMIT nulls — they are likely independent data gaps. Decision required at EDA.
3. **PURCHASES is a derived sum:** PURCHASES = ONEOFF_PURCHASES + INSTALLMENTS_PURCHASES. If all three are included in clustering, purchase behavior is triple-counted. This must be resolved in EDA before segmentation runs.

---

## Known Analytical Gotchas

1. **Frequency variables are bounded and likely zero-inflated.** Variables like CASH_ADVANCE_FREQUENCY, ONEOFF_PURCHASES_FREQUENCY, and PURCHASES_INSTALLMENTS_FREQUENCY will have large masses at exactly 0. Standard z-score normalization before clustering is still correct, but check the distribution shape of each frequency variable in EDA — if more than 40% of values are exactly 0, the variable may need to be split into a binary flag (ever/never) plus a conditional score for those who use the feature.
2. **BALANCE and PRC_FULL_PAYMENT tell opposite stories about the same customer.** A customer with high BALANCE and low PRC_FULL_PAYMENT is a classic revolver — they carry debt and pay the minimum. A customer with low BALANCE and high PRC_FULL_PAYMENT is a transactor — they spend and pay in full. These two variables together are the most important behavioral signal in the dataset. Profile each segment on both simultaneously.
3. **CASH_ADVANCE customers are behaviorally and financially distinct.** Do not let cash advance customers get absorbed into a "low purchase" or "dormant" segment based on their low PURCHASES score — their CASH_ADVANCE and CASH_ADVANCE_FREQUENCY values define their behavior. Check after clustering that at least one segment captures cash advance users as a primary characteristic.
4. **TENURE has very low variance.** With values ranging only from 6 to 12 months, TENURE is unlikely to be a meaningful segmentation variable. It may still be useful as a profiling descriptor after segments are formed — e.g. "Segment A has shorter average tenure than Segment B" — but should probably not be included in the clustering feature set. Exclude it from clustering unless EDA reveals meaningful behavioral differences by tenure band.
5. **Derived feature opportunity: BALANCE_TO_LIMIT_RATIO.** The ratio of BALANCE to CREDIT_LIMIT (utilization rate) is a standard credit risk metric and more meaningful than BALANCE alone. Consider deriving this variable at EDA and including it in clustering in place of raw BALANCE. Flag this as a decision for the analyst.

---

## Join Keys

| Key Column | Joins To | Notes |
|---|---|---|
| CUST_ID | Any customer-level dataset from the same credit card portfolio | CUST_ID is the join key if this analysis is extended with additional customer attributes (e.g. demographics, delinquency history, product holdings) |
