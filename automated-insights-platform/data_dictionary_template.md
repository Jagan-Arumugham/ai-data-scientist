# Data Dictionary

## Dataset Overview
- **File name:** [filename].csv
- **Row count:** [approximate, if known]
- **Grain:** [One row per _____. If unknown, leave blank — EDA node will determine.]
- **Snapshot date or time range:** [When was this data extracted? What period does it cover?]
- **Source system(s):** [Where did this data come from?]
- **Date last refreshed:** [When was the extract pulled?]


## Column Definitions

For each column, provide: the business meaning, how it was calculated or sourced, the unit or scale, and any known issues.

---

### Target and Outcome Variables
[Columns that represent the behavior you are trying to understand or predict]

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

### Flow and Financial Variables
[Columns related to money movement, balances, assets]

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

### Behavioral and Engagement Variables
[Columns related to digital activity, trading, product usage]

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

### Demographic Variables
[Columns related to client characteristics — age, wealth, tenure]

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

### Relationship Variables
[Columns related to products held, accounts, relationships with the firm]

| Column Name | Business Meaning | Calculation / Source | Unit / Scale | Known Issues |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

### Operational Identifiers
[Columns that are IDs or codes with no direct analytical value — flag these for likely exclusion]

| Column Name | What It Identifies | Should It Be Excluded? |
|---|---|---|
| | | Yes / No |
| | | Yes / No |


## Null Value Conventions
[Explain what null values mean in this dataset. Are they true missing values, structural zeros, or something else?]

| Column Name | Null Meaning | Treatment |
|---|---|---|
| | | |
| | | |


## Coded Values and Lookups
[If any columns contain coded values (e.g. 1=low, 2=medium, 3=high), define them here]

| Column Name | Code | Meaning |
|---|---|---|
| | | |
| | | |


## Known Data Quality Issues
[List any known problems with this dataset that the analytical nodes should be aware of before running]

1.
2.
3.


## Known Analytical Gotchas
[List any patterns in this data that could be misinterpreted without domain knowledge — seasonal effects, regulatory behaviors, population quirks, historical events that affect the data]

1.
2.
3.


## Join Keys
[If this dataset is intended to be joined with another dataset in future, list the join keys here]

| Key Column | Joins To | Notes |
|---|---|---|
| | | |
