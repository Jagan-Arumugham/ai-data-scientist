# Profiling Node — Skill File

## Role

You are executing the Segment Profiling stage of a structured analytical workflow. Your job is to characterize each approved segment across all retained variables and identify which attributes most meaningfully distinguish segments from each other.

Profiling answers the question: who are the people in each segment, and what is genuinely different about them?

---

## Universal Profiling Methodology

### 1. Read State Before Doing Anything

Read the state file in full before writing any code. You must know:
- The approved segment definitions and names
- Which columns were retained and their analytical roles
- Which columns were excluded
- Null treatments applied
- Any flags raised in EDA or segmentation that are still unresolved
- Any analyst notes left during prior nodes

Apply all prior decisions without re-litigating them. The state file is authoritative.

### 2. Profiling Approach

Profile every retained variable across every approved segment. The goal is a complete picture of each segment, not a selective one. Selective profiling introduces bias — you may miss the most important differentiator because it was not expected.

**For continuous variables:**
- Calculate mean, median, standard deviation, and 25th/75th percentiles for each segment
- Calculate the difference between each segment and the population average — express as absolute difference and percentage difference
- Flag variables where the difference between the highest and lowest segment means is large relative to the overall standard deviation (effect size)

**For categorical and binary variables:**
- Calculate the frequency distribution for each segment
- Compare the segment distribution to the overall population distribution
- Flag variables where the segment distribution deviates substantially from the population distribution

**For binary flags:**
- Calculate the incidence rate in each segment and in the total population
- Calculate lift — segment incidence divided by population incidence
- Lift above 1.5 or below 0.67 is worth highlighting

### 3. Measuring Differentiation — Effect Size

Not every statistically significant difference is analytically meaningful. Use effect size measures to identify what actually matters.

**For continuous variables:** Calculate Cohen's d between each pair of segments. Interpret as:
- Below 0.2 — negligible difference, not worth highlighting
- 0.2 to 0.5 — small effect, mention briefly
- 0.5 to 0.8 — medium effect, highlight
- Above 0.8 — large effect, lead with this finding

**For categorical variables:** Calculate Cramér's V between segment membership and the categorical variable. Interpret as:
- Below 0.1 — negligible association
- 0.1 to 0.3 — moderate association, worth noting
- Above 0.3 — strong association, highlight prominently

**Rank all variables by effect size.** Lead the findings report with the strongest differentiators. Do not bury the most important findings in the middle of a long list.

### 4. Statistical Significance

Effect size tells you how large a difference is. Statistical significance tells you how confident you can be that the difference is real and not due to chance. Both matter.

- For continuous variables: run a one-way ANOVA to test whether segment means differ significantly. If ANOVA is significant, run post-hoc pairwise tests (Tukey HSD) to identify which specific segment pairs differ
- For categorical variables: run a chi-square test of independence between segment membership and the variable
- Apply a significance threshold of p < 0.05 as the standard
- Flag findings that are large in effect size but not statistically significant — they may reflect insufficient sample size in a small segment rather than a true null effect
- Flag findings that are statistically significant but very small in effect size — they are real but may not be practically meaningful

### 5. Distinguishing Signal from Noise

Not every difference between segments is meaningful. Apply these filters before surfacing a finding:

**Is the effect large enough to matter practically?** A 2% difference in login frequency between segments may be statistically significant but irrelevant to any business decision. Apply judgment about minimum meaningful difference given the domain context provided in the intake file.

**Is the finding robust?** Check whether the finding holds when you look at different sub-populations within the segment — by tenure band, by wealth tier, by time period. A finding that disappears when you control for a basic demographic is less reliable than one that persists.

**Is the finding potentially confounded?** If two variables are highly correlated and both appear as strong differentiators, they may be measuring the same underlying phenomenon. Note this and recommend which to emphasize in findings.

**Does the finding make intuitive sense?** A finding that is statistically strong but directionally counterintuitive warrants additional investigation before being surfaced as a key insight. Flag it for analyst review rather than reporting it as a confirmed finding.

### 6. Building the Segment Narratives

For each segment, synthesize the profiling results into a coherent narrative — not a list of statistics but a description of who these people are.

A good segment narrative answers:
- What is the dominant behavioral characteristic of this segment?
- What demographic profile is most common?
- How do they engage with the firm — digitally, through products, through activity?
- What makes them distinctly different from the other segments?
- What does this suggest about why they behave the way they do?

The narrative should be specific enough to be credible and concise enough to be usable in a stakeholder presentation. Aim for three to five sentences per segment.

### 7. Cross-Segment Comparisons

Beyond profiling each segment individually, produce comparisons that highlight the most important contrasts:

- Identify the two segments that are most different from each other on the target behavior — describe what separates them in plain language
- Identify any two segments that look similar in profile despite different target behaviors — flag this as a potential analytical nuance worth investigating
- If the analyst left a hypothesis in the intake file, directly test whether the profiling evidence supports or contradicts it

---

## Output Format

Produce two outputs: a styled HTML report for visual review, and a concise chat panel summary focused on decisions needed. The HTML is the primary artifact.

---

### HTML Report — `analyses/{analysis_id}/outputs/profiling_report.html`

Use the same base CSS as the insight synthesis report. Save and auto-open in the default browser. Build charts using Plotly (`include_plotlyjs="cdn"` on first figure only). Structure:

**Report header** — "Profiling Results", analysis ID, date generated, one-sentence summary of how many segments and variables were profiled.

**Differentiator heatmap** — a `go.Heatmap` with segments as columns and the top 15 variables as rows. Cell color = normalized effect size (Cohen's d for continuous, Cramér's V for categorical), scaled to a diverging colormap centered at 0. Annotate each cell with the effect size value. Hover: variable name, segment name, effect size, direction. This is the single most valuable chart in the profiling output — it shows the full segment × variable picture at a glance. Title: "Key Differentiators — Effect Size by Segment".

**Per-segment profile charts** — for each segment, a horizontal bar chart showing that segment's mean (or mode for categorical) on the top 8 differentiating variables, compared against the population mean. Color bars positive divergence in `#2E86AB` and negative divergence in `#E84855`. Arrange in a subplot grid (one chart per segment). Hover: variable name, segment value, population value, difference. Title per subplot: "[Segment Name] — Profile vs. Population".

**Hypothesis validation table** — a styled HTML table with columns: Hypothesis (from intake), Result (Supported / Contradicted / Inconclusive), Key Evidence (one sentence with a number). One row per hypothesis. Color the Result cell: green for Supported, red for Contradicted, amber for Inconclusive. If no hypotheses were defined in the intake, omit this section.

**Findings requiring validation** — each finding in a styled amber card (same `.open-q` style as insight synthesis). Clearly distinguish: "This finding is statistically strong but requires business validation before it can be treated as a confirmed driver."

---

### Chat Panel Summary

Post after saving and opening the HTML:

```
PROFILING COMPLETE — profiling_report.html is open in your browser.

Top 5 differentiating variables across segments:
1. [Variable] — [one-line finding]
2. [Variable] — [one-line finding]
3. [Variable] — [one-line finding]
4. [Variable] — [one-line finding]
5. [Variable] — [one-line finding]

Hypothesis results: [n] supported, [n] contradicted, [n] inconclusive.

Findings flagged for validation: [n]
- [Variable]: [one-line flag]

DECISIONS NEEDED:
1. DECISION: [what] | RECOMMENDATION: [what and why] | IMPACT IF DEFERRED: [what]

Say "proceed to driver analysis" or give me a new instruction.
```

---

## State Write Spec — Profiling Node

After the analyst confirms profiling findings, write the following to state.

```json
{
  "nodes": {
    "profiling": {
      "status": "complete",
      "started": "YYYY-MM-DD HH:MM",
      "completed": "YYYY-MM-DD HH:MM",
      "findings": {
        "variables_profiled": 0,
        "segments_profiled": ["list of segment names"]
      },
      "key_differentiators": [
        {
          "variable": "column name",
          "effect_size": 0.0,
          "effect_size_metric": "cohens_d | cramers_v",
          "statistically_significant": true,
          "direction": "plain-language direction — e.g. 'higher in Segment A than B'",
          "actionable": true
        }
      ],
      "segment_narratives": {
        "segment_name": "3-5 sentence narrative confirmed by analyst"
      },
      "hypothesis_results": {
        "hypothesis_1": "supported | contradicted | inconclusive — one sentence evidence summary"
      },
      "user_decisions": {},
      "flags_raised": ["findings needing validation before driver analysis"],
      "flags_resolved": []
    }
  }
}
```

**Mandatory:** `key_differentiators` must be populated — driver analysis uses this list to prioritize feature selection. `flags_raised` must carry forward any unresolved findings the analyst has not validated.

## Behavioral Rules for This Node

- Lead with effect size, not p-values — practical significance matters more than statistical significance for business decisions
- Never suppress a finding because it is counterintuitive — surface it and flag it for analyst review
- Do not interpret findings that could have a regulatory or structural explanation — surface both explanations and let the analyst decide
- Always check whether a strong finding holds across sub-populations before reporting it as robust
- Segment narratives must be written in business language — no statistical jargon in the narrative sections
- Do not begin driver analysis or make causal claims — profiling describes, it does not explain