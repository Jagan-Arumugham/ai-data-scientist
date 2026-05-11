# Analysis Intake — Sample (Tenured Client Outflow)

## Business Question
Why are tenured clients not deepening their relationship with us — specifically, why are some clients taking money out rather than bringing more in? We want to understand the behavioral, demographic, and engagement characteristics that distinguish clients who outflow from those who do not, and identify actionable drivers we can influence.

## Dataset
- CSV file: `data/tenured_clients.csv`
- Data dictionary: `data/data_dictionary.md`

## Analysis Scope
- Population: Clients with tenure of 12 months or more as of the snapshot date. Clients below 12 months tenure are structurally different and should be excluded from the core analysis — they can be flagged separately if the data permits.
- Time period: Inflow and outflow figures cover the trailing 12 months from the snapshot date.
- Level of granularity: One row per client. If the grain appears to be per account, flag immediately — this will require a roll-up decision before analysis can proceed.

## Domain Conventions
- Null values in outflow_amount and inflow_amount represent zero — the client had no outflows or inflows in the period. Do not impute or treat as missing.
- Null values in last_trade_date mean the client has never traded — treat as non-trader, not as missing data.
- Null values in digital engagement columns (login_frequency, mobile_sessions) may indicate a client who has never used digital channels — treat as zero engagement, not as missing.
- options_flag was only tracked from mid-2023 onward — clients onboarded before this date may show false negatives on this field.

## Known Hypotheses Going In
1. Digital disengagement is a leading indicator of outflow — clients who are logging in less frequently are more likely to be moving money out.
2. Clients who hold only one product type (cash-heavy, not invested) are at higher outflow risk than multi-product clients.
3. The 65+ age cohort may show elevated outflow patterns that are regulatory in nature (RMD withdrawals) rather than behavioral dissatisfaction — this needs to be flagged and not conflated with sentiment-driven outflow.

## Known Risk Factors or Confounders
- Seasonal effects: if the data covers Q4 or Q1, outflow patterns may reflect year-end tax moves or RMD distributions — interpret with caution.
- Clients acquired via the 2022 acquisition may have tenure columns that were reset at acquisition date rather than original account open date — if tenure analysis looks anomalous, this is the likely cause.
- High-wealth clients (top wealth tier) may show large absolute outflows that are actually normal rebalancing behavior — consider whether to analyze by absolute flow or flow as a percentage of AUM.

## Nodes to Run
- [x] EDA
- [x] Segmentation
- [x] Profiling
- [x] Driver Analysis
- [x] Insight Synthesis

Nodes to skip: none

## Stakeholder Context
Primary audience is the Head of US Wealth Management and the Product team. They are comfortable with high-level statistical framing but want findings expressed in business language with specific client counts and dollar impact where possible. They have limited patience for methodology detail — keep that in an appendix. They respond well to segment-level recommendations with clear targeting logic.

## Prior Analyses to Be Aware Of
A similar analysis was conducted 18 months ago. The key finding at the time was that clients who did not invest within 90 days of funding their account attrited at a significantly higher rate. That analysis focused on new clients. This analysis focuses on tenured clients — a different population with different dynamics. Do not assume the same drivers apply.

## Output Required
A structured findings document suitable for conversion into a 10 to 12 slide executive presentation. The document should include an executive summary, key findings with supporting evidence, segment profiles, prioritized recommendations, and a section on open questions and limitations.
