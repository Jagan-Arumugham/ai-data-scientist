# Analysis Intake

## Business Question
[State the core question the analysis must answer. Be specific about the behavior you are trying to understand and the population you are analyzing.]


## Dataset
- CSV file: `data/[filename].csv`
- Data dictionary: `data/[filename]_data_dictionary.md`


## Analysis Scope
- Population: [Who is included in this analysis? Any filters applied before you received the data?]
- Time period: [What time window does this data cover?]
- Level of granularity: [One row per client? Per account? Per transaction? If you don't know, leave blank — the EDA node will determine it.]


## Domain Conventions
[List any dataset-specific conventions the analytical nodes must respect. These are facts about how this data was constructed — not analytical decisions.]

Examples:
- Null values in [column] mean [interpretation]
- [Column] was only tracked from [date] onward — earlier records may show false negatives
- Clients acquired via [event] may have [column] artificially reset
- [Column] reflects [specific calculation methodology]


## Known Hypotheses Going In
[List any hypotheses you want the analysis to test or keep in mind. These are starting points, not conclusions.]

1.
2.
3.


## Known Risk Factors or Confounders
[List any factors that might confound the analysis or produce misleading signals if not accounted for.]

Examples:
- Seasonal effects in [month range] may inflate [column]
- Regulatory behavior in [population segment] may look like [behavioral signal] but is structural
- [Column] is self-reported and may be stale


## Nodes to Run
[Check the nodes you want included in this analysis run. All nodes run by default.]

- [x] EDA
- [x] Segmentation
- [x] Profiling
- [x] Driver Analysis
- [x] Insight Synthesis

Nodes to skip and reason:
- [node name]: [reason for skipping]


## Stakeholder Context
[Optional. Who will receive the output of this analysis? What level of statistical detail vs. business narrative do they prefer? Any specific framing they have asked for?]


## Prior Analyses to Be Aware Of
[Optional. Has a similar analysis been run before? What did it find? What changed since then that motivated this new analysis?]


## Output Required
[What does the final output need to be? A structured findings document? A PowerPoint-ready narrative? A set of recommendations with supporting evidence?]
