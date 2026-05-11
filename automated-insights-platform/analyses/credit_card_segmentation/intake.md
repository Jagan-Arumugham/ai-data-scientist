# Analysis Intake — Credit Card Customer Segmentation

## Business Question
What distinct behavioral segments exist among our active credit card customers, and what does each segment's usage pattern reveal about their financial behavior, engagement level, and relationship with the product? The goal is to move beyond a single undifferentiated customer base and produce named, interpretable segments that can inform differentiated marketing strategy, credit risk posture, and product design.

This is an exploratory segmentation — there is no predefined target variable. The segments themselves are the deliverable.

---

## Dataset
- CSV file: `data/cc_general.csv`
- Data dictionary: `data/data_dictionary.md`

---

## Analysis Scope
- Population: Active credit card holders with account activity in the last 6 months. Inactive or dormant accounts were excluded prior to data extraction.
- Time period: 6-month behavioral snapshot. All variables summarize behavior over the same 6-month window.
- Level of granularity: One row per customer account.

---

## Domain Conventions

- **No target variable.** This is a pure unsupervised problem. The segmentation node must use clustering — do not attempt rule-based segmentation on a proxy target. Confirm approach with analyst before running.
- **CREDIT_LIMIT has nulls.** These are structurally missing — likely accounts where credit limit data was not available at extraction. Do not impute with mean. Flag the affected rows and decide with analyst whether to exclude or carry forward with a median fill.
- **MINIMUM_PAYMENTS has nulls.** Same treatment as CREDIT_LIMIT — structural missingness, not behavioral. Flag and decide.
- **BALANCE_FREQUENCY, PURCHASES_FREQUENCY, ONEOFF_PURCHASES_FREQUENCY, PURCHASES_INSTALLMENTS_FREQUENCY, CASH_ADVANCE_FREQUENCY, PRC_FULL_PAYMENT** are all scored on a 0-to-1 scale where 1 = maximum frequency or full payment. These are not raw counts — they are normalized behavioral scores. Do not treat them as continuous variables with the same scale as raw dollar amounts.
- **CASH_ADVANCE and CASH_ADVANCE_FREQUENCY together** describe a distinct behavioral pattern — customers who use their credit card as a short-term loan rather than a purchase instrument. These two variables should be analyzed together in profiling.
- **ONEOFF_PURCHASES and INSTALLMENTS_PURCHASES** sum to total PURCHASES. They are not independent — including all three in the same clustering run will double-weight purchase behavior. Decide at EDA which to retain.
- **TENURE** ranges from 6 to 12 months in this dataset. All customers are relatively recent or have been tracked for the same window. Low variance in tenure may limit its utility as a segmentation variable.

---

## Known Hypotheses Going In

1. A segment of high-balance, low-purchase customers exists — customers who carry balances but do not actively use the card for purchases. These are likely revolvers generating interest income.
2. A segment of high-frequency, low-balance transactors exists — customers who use the card regularly for purchases and pay in full each month. These are the most engaged but potentially least profitable from an interest perspective.
3. A cash advance segment exists — customers whose primary card usage is cash withdrawal rather than purchases. This is a behaviorally and financially distinct group with a different risk profile.
4. A dormant or minimal-usage segment exists — customers with low balance, low purchase frequency, and low payments. These are at risk of product abandonment or attrition.
5. Installment purchasers form a distinct segment from one-off purchasers — customers who consistently split purchases into installments may have different financial constraints and risk profiles than those who make large one-off purchases.

---

## Known Risk Factors or Confounders

- **PURCHASES, ONEOFF_PURCHASES, and INSTALLMENTS_PURCHASES are intercorrelated by construction** — PURCHASES = ONEOFF_PURCHASES + INSTALLMENTS_PURCHASES. Including all three in clustering will artificially inflate the weight of purchase behavior. Retain ONEOFF_PURCHASES and INSTALLMENTS_PURCHASES and exclude PURCHASES, or retain PURCHASES and exclude the two components. Decide at EDA.
- **BALANCE and CREDIT_LIMIT are related** — a high balance on a low credit limit means something different than the same balance on a high limit. Consider deriving a BALANCE_TO_LIMIT_RATIO feature if it adds interpretability.
- **Frequency variables are bounded at 0 and 1** — their distributions will be skewed with mass at the extremes. Standard z-score normalization before clustering is still correct, but flag if a variable has more than 30% of values at exactly 0 or exactly 1 — this means it may behave more like a binary variable than a continuous one.
- **Short tenure customers** (TENURE = 6) may have artificially low values on cumulative variables like PURCHASES_TRX and CASH_ADVANCE_TRX simply because they have had less time to accumulate transactions. Consider whether TENURE should be used as a segmentation variable or a control variable.
- **PAYMENTS and MINIMUM_PAYMENTS** — a customer who always pays the minimum is behaviorally very different from one who pays in full, but both may show similar PAYMENTS values if their balances are similar. PRC_FULL_PAYMENT is the cleaner variable for capturing repayment behavior.

---

## Nodes to Run

- [x] EDA
- [x] Segmentation
- [x] Profiling
- [ ] Driver Analysis
- [x] Insight Synthesis

Nodes to skip:
- **Driver Analysis:** There is no target variable to model against. Skip this node. Profiling will surface the key differentiators across segments, which serves the same analytical purpose for this use case.

---

## Stakeholder Context
Primary audience is the Credit Card Product and Marketing team. They want actionable segment profiles — who each group is, what they do with their card, and what product or communication strategy is most appropriate for each segment. They are comfortable with behavioral descriptions but not statistical methodology. Output should be business-language findings with customer counts and behavioral summaries per segment.

A secondary audience is the Credit Risk team, who want to understand whether any segment has an elevated risk profile based on cash advance usage, balance-to-limit ratios, or payment behavior.

---

## Prior Analyses to Be Aware Of
None — this is the first segmentation run on this dataset. Findings will serve as the baseline customer taxonomy for this credit card portfolio.

---

## Output Required
A structured findings document with: an executive summary, segment profiles (one per approved segment) with customer counts and behavioral summaries, a prioritized set of marketing and product recommendations per segment, and a note on any segments flagged for risk review. The segment profiles should be written at the level of detail needed to brief a campaign team — specific enough to design targeting criteria, not just descriptive labels.
