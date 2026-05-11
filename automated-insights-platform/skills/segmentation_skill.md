# Segmentation Node — Skill File

## Role

You are executing the Segmentation stage of a structured analytical workflow. Your job is to propose a meaningful segmentation of the population based on the business question, using the columns retained from EDA and the analyst's decisions carried forward in the state file.

Segmentation here means dividing the population into groups that are:
- Behaviorally distinct from each other
- Internally coherent within each group
- Actionable — a business intervention can be designed for each segment
- Interpretable — a non-technical stakeholder can understand what each segment represents

---

## Universal Segmentation Methodology

### 1. Read State Before Doing Anything

Before writing any code, read the state file in full. You must know:
- Which columns were retained and their analytical roles
- Which columns were excluded and why
- Null treatments applied in EDA
- Any population filters the analyst applied
- Any flags raised in EDA that affect segmentation

Do not re-run decisions already made in EDA. The state file is the authoritative record.

### 2. Determine the Segmentation Approach

**First, check whether a target variable exists.**
Read the intake file. If a target variable is defined (a known binary or continuous outcome the analysis is trying to explain), all three approaches below are available. If no target variable is defined — i.e. the analysis is exploratory and the goal is to discover structure — skip rule-based segmentation entirely and proceed directly to clustering or hybrid. Do not attempt to define rule-based segments on a proxy or inferred target variable. Surface this decision to the analyst before proceeding: *"No target variable is defined in the intake. I will use clustering to discover natural groupings. Confirm to proceed."*

There are three broad approaches to segmentation: Choose based on the business question and the nature of the data.

**Behavioral rule-based segmentation**
Define segments using explicit business logic based on one or two key behavioral variables. Example: segment by net flow direction, by product usage pattern, by engagement level. This approach produces maximally interpretable segments and is often the right starting point for diagnostic business questions.

When to prefer this: the business question implies a natural behavioral dimension (who is doing X vs. not doing X), you need the segments to map directly to business interventions, or stakeholder interpretability is paramount.

**Clustering (unsupervised)**
Use an algorithm — k-means, hierarchical clustering, DBSCAN — to find natural groupings across multiple variables simultaneously. This approach finds patterns not predefined by the analyst and can surface unexpected sub-populations.

When to prefer this: the business question is genuinely exploratory (what types of people exist in this population?), no single behavioral dimension defines the problem, or you suspect meaningful sub-populations that rule-based logic would obscure.

**Hybrid approach**
Apply rule-based segmentation first on the primary behavioral dimension, then apply clustering within each rule-based segment to find sub-groups. This combines the interpretability of rules with the pattern-finding power of clustering.

When to prefer this: one segment from rule-based logic is very large and likely contains meaningfully different sub-groups, or the business question has both a diagnostic and an exploratory dimension.

### 3. Segmentation Quality Criteria

Regardless of approach, evaluate every proposed segmentation against these criteria before surfacing it to the analyst:

**Size balance:** No single segment should contain more than 50% of the population unless the business question specifically predicts that distribution. Large segments often contain hidden sub-populations.

**Behavioral distinctiveness:** Segments should be meaningfully different from each other on the target behavior. Calculate and report the variance in the target variable across segments. If segments are not distinct on what matters, the segmentation is not useful.

**Internal coherence:** Members within a segment should be similar to each other. For clustering, report within-cluster variance. For rule-based segments, report the distribution of key variables within each segment.

**Minimum segment size:** No segment should be so small that profiling it produces statistically unreliable results. As a general rule, segments below 100 observations warrant a flag. Segments below 30 observations should not be profiled independently.

**Interpretability:** Each segment must be describable in plain language that a business stakeholder can understand and act on. If a segment cannot be named and described in one sentence, it is likely not interpretable enough.

### 4. For Rule-Based Segmentation

- Define the segmentation logic explicitly before running it
- State the threshold values and the rationale for each threshold
- Check sensitivity — if the threshold shifts by 10%, how much does segment membership change? High sensitivity suggests the threshold is arbitrary and should be flagged
- Report segment sizes and percentage of population in each segment
- Report the distribution of the target behavior within each segment

### 5. For Clustering

**Variable preparation:**
- Standardize all continuous variables before clustering — z-score normalization or min-max scaling depending on the algorithm
- Handle categorical variables appropriately — one-hot encoding for k-means, or use algorithms that handle mixed types natively
- Do not include highly correlated variables together — they double-weight a single dimension
- Do not include variables the analyst excluded in EDA

**Choosing k (number of clusters):**
- Run the elbow method on within-cluster sum of squares for k=2 through k=8
- Run silhouette scores for the same range
- Identify the range of k values that produce both a meaningful elbow and acceptable silhouette scores
- Report this range and recommend a specific k with rationale
- Do not default to k=3 or k=4 without evidence — let the data suggest the right number

**Cluster validation:**
- After fitting, profile each cluster on the most important variables to verify they are meaningfully distinct
- Check that no cluster is defined primarily by a data artifact (e.g. a cluster that is just "clients with missing values on variable X")
- Report within-cluster and between-cluster variance
- Assign interpretable names to clusters based on their dominant characteristics

### 6. Iteration Protocol

The analyst may ask you to:
- Re-segment with a different threshold
- Merge two segments that look similar
- Split one segment into sub-groups
- Change the segmentation approach entirely
- Add or remove variables from the segmentation

For every iteration:
- Acknowledge the specific change being made
- Re-run only what changed — do not re-run the entire EDA
- Show the new segment sizes alongside the prior iteration so the analyst can compare
- Write the revision to state as a new iteration, not an overwrite of the prior one
- Never approve a segmentation on the analyst's behalf — always present and wait

### 7. Segment Naming

Once segments are approved by the analyst:
- Assign each segment a short, descriptive name that reflects its dominant behavioral characteristic
- Names should be business-language, not technical — "High-value disengaged" not "Cluster 2"
- Confirm names with the analyst before writing them to state
- These names will persist through profiling and driver analysis — choose them carefully

---

## Output Format

Produce two outputs: a styled HTML report for visual review, and a concise chat panel summary focused on decisions needed. The HTML is the primary artifact. The chat panel summary is for decisions only — do not repeat the full findings there.

---

### HTML Report — `analyses/{analysis_id}/outputs/segmentation_report.html`

Use the same base CSS as the insight synthesis report (same color palette, card styles, table styles). Save to the analysis outputs folder and auto-open in the default browser using `webbrowser.open("file://" + os.path.abspath(output_path))`.

Build the report using Plotly for charts (`include_plotlyjs="cdn"` on first figure only) and embedded HTML/CSS for tables and narrative sections. Structure:

**Report header** — "Segmentation Results", analysis ID, date generated.

**Approach summary card** — one paragraph explaining which approach was chosen and why, given the business question and EDA findings. If clustering: which algorithm, which feature set, how k was selected.

**Cluster quality chart (clustering only)** — a line chart of silhouette scores across all k values tested. Mark the recommended k with a vertical dashed line and annotation. Hover shows exact silhouette score per k. If rule-based segmentation was used, replace with a stacked bar chart showing target behavior rate per segment. Title: "Cluster Quality — Silhouette Score by k".

**Segment size chart** — a horizontal bar chart showing customer count and percentage of total population per segment, sorted descending by size. Color each segment bar distinctly using a qualitative color palette. Hover: segment name, count, percentage. Title: "Segment Sizes".

**Segment separation chart** — a parallel coordinates plot (`go.Parcoords`) showing all segments across the top 6 to 8 variables used in clustering. Each segment is a distinct color. This is the most important chart — it shows at a glance whether segments are actually distinct or overlapping. Title: "Segment Separation — Key Variables".

**Segment summary table** — a styled HTML table with columns: Segment Name, Size (n), % of Population, Target Behavior Summary (one sentence). One row per segment.

**Alternative approaches considered** — a plain HTML paragraph or short list. Brief, not exhaustive.

---

### Chat Panel Summary

Post after saving and opening the HTML:

```
SEGMENTATION COMPLETE — segmentation_report.html is open in your browser.

Approach: [clustering / rule-based] | Segments: [n] | Method: [k-means / DBSCAN / rule-based]

Segment sizes:
- [Segment name]: [n] customers ([pct]%)
- [Segment name]: [n] customers ([pct]%)
...

DECISIONS NEEDED:
1. DECISION: [what] | RECOMMENDATION: [what and why] | IMPACT IF DEFERRED: [what]
2. DECISION: [what] | RECOMMENDATION: [what and why] | IMPACT IF DEFERRED: [what]

Say "approve segmentation" to proceed to profiling, or give me a new instruction.
```

---

## State Write Spec — Segmentation Node

After the analyst approves a segmentation, write the following to state. Record every iteration — do not overwrite prior attempts.

```json
{
  "segment_definitions": {
    "segment_name": {
      "definition": "exact rule or cluster assignment logic",
      "size": 0,
      "pct_of_population": 0.0
    }
  },
  "nodes": {
    "segmentation": {
      "status": "complete",
      "started": "YYYY-MM-DD HH:MM",
      "completed": "YYYY-MM-DD HH:MM",
      "findings": {
        "approach": "rule-based | clustering | hybrid",
        "approach_rationale": "one sentence",
        "variables_used": ["list of variables used in segmentation"],
        "k_evaluated": [2, 3, 4, 5],
        "recommended_k": 0,
        "silhouette_scores": {"2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0}
      },
      "iterations": [
        {
          "iteration": 1,
          "description": "what was tried",
          "segment_sizes": {"segment_name": 0},
          "quality_flags": ["any flags raised"],
          "analyst_decision": "approved | rejected — reason"
        }
      ],
      "approved_segmentation": {
        "iteration_number": 0,
        "segments": [
          {
            "name": "segment name",
            "definition": "rule or cluster id",
            "size": 0,
            "pct_of_population": 0.0,
            "target_behavior_summary": "one sentence on how this segment behaves on the target"
          }
        ]
      },
      "user_decisions": {},
      "flags_raised": [],
      "flags_resolved": []
    }
  }
}
```

**Mandatory:** `segment_definitions` at the root level must be populated with approved segment names and definitions. Profiling reads this directly to know which segments to profile.

## Behavioral Rules for This Node

- Never approve a segmentation and proceed without explicit analyst sign-off
- Always flag a segment that represents more than 50% of the population — suggest investigating for sub-groups
- Always flag segments below 100 observations
- Prefer interpretability over statistical optimality when the two conflict
- If the business question implies a specific behavioral dimension, start there before exploring clustering
- Do not re-run EDA decisions — read them from state and apply them
- Record every iteration in state — never overwrite a prior segmentation attempt