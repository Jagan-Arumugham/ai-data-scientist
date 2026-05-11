# EDA Node — Skill File

## Role

You are executing the Exploratory Data Analysis stage of a structured analytical workflow. Your job is to produce a thorough, analyst-quality profile of the dataset that gives the human analyst everything they need to make informed decisions about how to proceed.

You are not solving the business question yet. You are understanding the data — its structure, quality, distributions, and relationships — well enough to proceed to segmentation with confidence.

---

## Universal EDA Methodology

### 1. Establish the Grain First

Before anything else, determine what one row represents. This is the most fundamental fact about any dataset and the most common source of analytical error when it is wrong or assumed.

- Count total rows
- Identify candidate key columns — IDs, dates, names — and check their uniqueness
- If a single column has row-count-level uniqueness, it is likely the primary key and defines the grain
- If no single column is unique but a combination is, the grain is composite — name it explicitly
- If you cannot determine the grain from the data, flag it immediately as a decision needed before proceeding
- Count distinct values of key identifier columns and compare to row count to surface duplicates

### 2. Dataset Overview

- Total rows and columns
- Grain statement: "One row represents one [entity] as of [time period]"
- Date range of the data if temporal columns are present
- Any immediate structural concerns that would compromise the analysis

### 3. Data Quality Assessment

Run a comprehensive quality check across every column:

**Missingness:**
- Calculate null rate for every column
- Classify each null: is it a true missing value, a structural zero, or an indicator of non-occurrence?
- Flag any column with null rate above 20% — state the null rate and recommend a treatment
- Treatments to consider: exclude the column, impute with mean/median/mode, treat as zero, treat as a binary flag indicating non-occurrence

**Duplicates:**
- Check for fully duplicate rows
- Check for partial duplicates on the key identifier — same entity appearing more than once
- If duplicates exist, determine whether they are data quality issues or expected (e.g. multiple time periods per entity)

**Data type integrity:**
- Flag columns whose values do not match their apparent type — numeric columns stored as strings, date columns stored as objects
- Flag columns with mixed types

**Value range validity:**
- Flag impossible values — negative ages, percentages above 100, dates in the future when not expected
- Flag columns where minimum and maximum are implausibly far apart — may indicate miscoding or outliers

**Cardinality check:**
- Calculate the number of distinct values for every column
- Flag any column where distinct value count is close to total row count — likely an identifier, not an analytical variable
- Flag any column with only one unique value — zero variance, analytically useless

### 4. Variable Classification

Group every column into one of these categories:
- **Target variable candidates** — the behavior being studied
- **Segmentation variables** — likely to define meaningful sub-groups
- **Profiling variables** — useful for characterizing segments but not for defining them
- **Control variables** — demographic or structural variables needed to avoid confounding
- **Temporal variables** — dates or time-based columns
- **Operational identifiers** — IDs, codes, system fields with no direct analytical value — recommend exclusion

### 5. Univariate Distributions — Key Variables First

For every retained variable, describe its distribution. Lead with the variables most relevant to the business question — do not bury them at the bottom.

For continuous variables report:
- Mean, median, standard deviation
- Min, max, and 25th/75th percentiles
- Skewness — right-skewed, left-skewed, or approximately normal
- Presence of outliers — are they plausible extreme values or likely data errors?
- Bimodal distributions — flag immediately, they often indicate a hidden population split that should be addressed before segmentation

For categorical and binary variables report:
- Frequency distribution of top values
- Whether any single category dominates (above 80% concentration)
- Whether the variable has enough variance to be analytically useful

### 6. Bivariate Relationships

**Correlation analysis:**
- Calculate pairwise correlations across all continuous variables
- Flag any pair with absolute correlation above 0.70 — they are likely redundant; recommend which to retain
- Flag any pair with absolute correlation above 0.90 — near-certain redundancy; strongly recommend dropping one
- Note: correlation measures linear relationships; flag cases where a non-linear relationship may be more appropriate

**Relationship to target behavior:**
- If the target variable or target behavior is identifiable from the intake file, examine its relationship with every other key variable
- Rank variables by strength of relationship to the target behavior
- Note: these are univariate relationships — they do not account for interactions or confounding

### 7. Outlier Assessment

- Identify outliers using IQR method (values below Q1 - 1.5×IQR or above Q3 + 1.5×IQR) for all continuous variables
- Distinguish between:
  - Plausible extreme values — real observations at the tail of the distribution
  - Data errors — values that are impossible or implausible given domain context
  - Influential outliers — values that will distort means and models if retained
- Recommend treatment for each type: retain, cap at percentile threshold, or exclude

### 8. Population Segments Worth Flagging Early

Before segmentation runs, identify any natural breaks in the data that the analyst should be aware of:
- Bimodal distributions that suggest two distinct sub-populations
- Variables with step-changes at specific values
- Combinations of variables that together define structurally distinct groups
- These are observations, not segmentation decisions — surface them and let the analyst decide

---

## Output Format

Produce output in two parts: a standalone interactive HTML report for visual review, and a concise text summary for the chat panel. The HTML report is the primary review artifact. The text summary is a brief companion, not a repeat of everything in the HTML.

---

### Libraries and Setup

Use the following libraries: `pandas`, `numpy`, `plotly.graph_objects`, `plotly.express`, `plotly.subplots`. Do not use matplotlib or seaborn for chart generation — all charts are Plotly.

Install if needed:
```bash
pip install plotly
```

At the top of the generation script, set a consistent theme:
```python
import plotly.io as pio
pio.templates.default = "plotly_white"
COLOR_GROUP_1 = "#2E86AB"
COLOR_GROUP_2 = "#E84855"
COLOR_NEUTRAL = "#6C757D"
COLOR_FLAG_RED = "#E84855"
COLOR_FLAG_AMBER = "#F4A261"
COLOR_FLAG_GREEN = "#2A9D8F"
```

All charts are assembled into a single `plotly.subplots` figure or collected as individual `go.Figure` objects and written to a single HTML file. The output path is always relative to the analysis folder — `analyses/{analysis_id}/outputs/eda_charts/eda_report.html`. Construct the path from the active `analysis_id` at runtime:
```python
import os
from plotly.subplots import make_subplots

output_dir = os.path.join("analyses", analysis_id, "outputs", "eda_charts")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "eda_report.html")

with open(output_path, "w") as f:
    f.write("<html><head><title>EDA Report</title></head><body>\n")
    for fig in figures:
        f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    f.write("</body></html>")
```

Use `include_plotlyjs="cdn"` for the first figure only, and `include_plotlyjs=False` for all subsequent figures to avoid embedding the Plotly library multiple times.

---

### Available Interactions — Applied Per Chart Type

Every chart produced by this node is interactive. The following interactions are available and should be deliberately configured:

**Universal interactions (all chart types):**
- **Hover tooltips** — configure `hovertemplate` on every trace to show exact values, counts, and percentages. Never leave hover as the Plotly default — always write an explicit template so the tooltip is readable in business language, not variable-name language.
- **Zoom** — box zoom by click-drag, scroll zoom with mouse wheel. Enable scroll zoom on every figure: `fig.update_layout(dragmode="zoom")`.
- **Pan** — available after zooming in. No configuration needed.
- **Reset axes** — double-click to return to full view. No configuration needed.
- **Download PNG** — built-in Plotly toolbar. No configuration needed.
- **Linked axes zoom** — when charts share an axis via `shared_xaxes=True` or `shared_yaxes=True` in `make_subplots`, zooming one chart zooms all charts that share that axis. Use this for all grid layouts where variable comparisons are the goal.

**Histogram-specific:**
- Set `nbinsx` explicitly — do not let Plotly auto-bin. Calculate a sensible bin count based on the variable's range and grain.
- Add a vertical mean line using `fig.add_vline(x=mean_val, line_dash="dash", annotation_text="Mean")`.
- Use `barmode="overlay"` with `opacity=0.65` when overlaying two distributions (e.g. the two groups defined by the target variable on the same histogram). This makes the comparison interactive — legend clicks show/hide each group.

**Bar chart-specific:**
- Sort bars descending by value before plotting — Plotly does not auto-sort.
- Add percentage labels as text on each bar using `texttemplate="%{text:.1f}%"` and `textposition="outside"`.
- Color bars conditionally based on thresholds (e.g. null rate traffic light) by building a color list in Python before passing to `go.Bar`.

**Scatter plot-specific:**
- Enable box select and lasso select: `fig.update_layout(dragmode="select")`.
- Color points by the target variable groups (read group labels from the intake file) using the palette constants defined at setup.
- Add a regression line using `plotly.express.scatter` with `trendline="ols"` — this renders on hover with the slope and R² value.
- Set `hover_data` to include columns not on the axes — read the intake file to identify which grouping or categorical variables are most meaningful for this analysis, and include those.

**Box plot-specific:**
- Set `boxpoints="outliers"` to render individual outlier points as dots. On hover, each point shows its exact value.
- Use `orientation="h"` for horizontal layout when comparing many variables side by side.

**Heatmap-specific (correlation matrix):**
- Use `go.Heatmap` with `colorscale="RdBu"`, `zmid=0`, `zmin=-1`, `zmax=1`.
- Set `hovertemplate` to: `"<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>"`.
- Mask the upper triangle by setting those cells to `None` before plotting.
- Add text annotations for the correlation values using `texttemplate="%{z:.2f}"`.

**Dropdown menus:**
- Use Plotly's `updatemenus` for charts where the analyst may want to switch between variables (e.g. viewing distributions of different continuous variables on one chart). Build a dropdown that swaps the `x` data source.
- Example use: the continuous variable distributions section — instead of a static grid, offer a single histogram with a dropdown to switch between variables. This keeps the report compact and supports rapid variable switching.

---

### Part 1 — Interactive HTML Report (Primary Output)

Generate a single HTML file saved to `analyses/{analysis_id}/outputs/eda_charts/eda_report.html`. Structure the report as a sequence of titled sections, each containing one or more Plotly figures. Add a plain-HTML section header (`<h2>`) between sections for readability.

#### Section 1 — Dataset Overview
Plain HTML block (no chart). State: row count, column count, grain statement, date range if applicable, any immediate structural flags. Style with a light background card for visual separation.

#### Section 2 — Missingness Profile
A horizontal bar chart showing null rate (%) for every column, sorted descending by null rate. Color bars using the traffic light scheme: red if null rate exceeds 20%, amber if between 5% and 20%, green below 5%. Add a vertical dashed line at the 20% threshold using `fig.add_vline`. Hover tooltip: column name, null count, null rate %, and the recommended treatment from the intake domain conventions where applicable. Title: "Null Rate by Column — Flag if Above 20%".

#### Section 3 — Target Variable Distribution
If the target is binary: a bar chart of class counts with percentage labels and hover showing exact count and share. Color bars using the palette constants — first group `COLOR_GROUP_1`, second group `COLOR_GROUP_2`. Read group labels from the intake file. If the target is continuous: a histogram with KDE overlay using `go.Histogram` and `go.Scatter` (KDE calculated in scipy), with a vertical mean line. Title: "Distribution of [Target Variable Name]".

#### Section 4 — Continuous Variable Distributions
For each continuous variable retained after removing operational identifiers, produce a histogram with KDE overlay. Use a dropdown menu to switch between variables — one interactive chart, not a static grid. For each variable view: show mean line, annotate with mean, median, standard deviation, and null rate in the chart's subtitle or annotation box. Flag bimodal distributions by adding a subtitle note: "⚠ Possible bimodal distribution — review before segmentation." Hover tooltip: bin range, count, percentage of total. Order variables in the dropdown by relevance to the business question as stated in the intake file — lead with the variables most directly related to the target behavior, follow with supporting variables.

#### Section 5 — Target Variable Split Distributions
For the top 8 continuous variables most correlated with the target variable, produce overlaid histograms comparing the two populations defined by the target variable — read the target variable name and its group labels from the intake file. Use a dropdown to switch between variables. Set `barmode="overlay"`, `opacity=0.65`. Color each group using the palette constants — the first group uses `COLOR_GROUP_1`, the second uses `COLOR_GROUP_2` (or reassign to `COLOR_NEUTRAL` if the target is not binary). Hover tooltip: group label (from intake), bin range, count, percentage within group. Title: "[Target Variable Name] — Distribution Comparison by Group". This is the single most analytically valuable chart in the EDA — surface it prominently.

#### Section 6 — Outlier Summary
For each continuous variable, produce a horizontal box plot using `go.Box` with `boxpoints="outliers"`. Stack all variables in a single chart using `make_subplots` with shared x-axis. Hover tooltip on outlier points: exact value and variable name. Hover tooltip on box: Q1, median, Q3, IQR, outlier count. Title: "Outlier Summary — All Continuous Variables".

#### Section 7 — Correlation Heatmap
Full correlation matrix heatmap for all continuous variables. Use `go.Heatmap` with `colorscale="RdBu"`, `zmid=0`. Mask upper triangle. Add text annotations for values. Hover tooltip: variable pair names and exact correlation value. Cells where absolute correlation exceeds 0.70 should be visually distinguished — add a border or annotation marker. Title: "Correlation Matrix — Pairs Above 0.70 Flagged".

#### Section 8 — Bivariate Scatter: Top Drivers vs. Target
For the top 6 continuous variables most correlated with the target, produce scatter plots against the target variable. Color points by target variable groups (read labels from intake file) using the palette constants. Add OLS trendline. Enable lasso select so the analyst can select a cluster of points and inspect them. Hover tooltip: row identifier if available, variable value, target value, and any key grouping variables present in the dataset (e.g. segment, tier, category). Use `make_subplots` in a 2×3 grid with linked x-axis zoom where applicable. Title each subplot: "[Variable] vs [Target Variable]".

#### Section 9 — Categorical Variable Distributions
For each categorical variable, produce a horizontal bar chart of value frequencies, sorted descending. Show count and percentage. Color bars — flag any single category above 80% share in COLOR_FLAG_RED. Add a dropdown to switch between categorical variables. Hover tooltip: category name, count, percentage of total. Title: "Categorical Variable Distributions".

#### Section 10 — Data Quality Summary Table
Render a sortable HTML table (using `plotly.graph_objects.Table`) showing every column with: data type, null count, null rate (%), distinct value count, and a Flag column populated for columns with null rate above 20%, cardinality above 80% of row count, or only one unique value. Color flagged rows in a light red background. Hover is not needed here — this is a reference table.

---

### Part 2 — Chat Panel Text Summary (Companion Output)

After generating and saving the HTML report, post a concise text summary in the chat panel. This is not a repeat of the report — it is a brief orientation and a prioritized list of decisions needed.

Structure:

**EDA COMPLETE — Open the interactive report at `analyses/{analysis_id}/outputs/eda_charts/eda_report.html`**

*Open in any browser. All charts support hover, zoom, pan, and legend filtering. Section 5 (target variable split distributions) is the highest-value section — start there.*

**Dataset:** [row count] rows, [column count] columns. Grain: [one row per ___].

**Top data quality flags (Section 2 of the report):**
- [Column]: [null rate]% nulls — [recommendation]
- [Column]: [issue] — [recommendation]

**Most important distributions to review (Sections 4 and 5):**
- [Variable]: [one-line observation — e.g. "heavily right-skewed, possible bimodal split around [value]"]
- [Variable]: [observation]

**Correlation flags (Section 7):**
- [Column A] and [Column B]: correlation [value] — recommend dropping [one]

**DECISIONS NEEDED before segmentation:**
1. **DECISION:** [what] | **RECOMMENDATION:** [what and why]
2. **DECISION:** [what] | **RECOMMENDATION:** [what and why]
3. **DECISION:** [what] | **RECOMMENDATION:** [what and why]

**Columns recommended for exclusion:** [comma-separated list with one-word reason each]

**Ready for your instruction. You can:**
- Tell me which columns to drop or retain
- Ask me to investigate a specific variable further
- Ask me to re-run a specific chart with different parameters
- Say "proceed to segmentation" when you are satisfied

---

## State Write Spec — EDA Node

After the analyst confirms their decisions at the end of this node, write the following structure to `analyses/{analysis_id}/state.json`. This schema is what downstream nodes depend on — populate every field.

```json
{
  "columns_excluded": ["list of column names excluded, with one-word reason each"],
  "columns_retained": ["list of all column names retained for downstream analysis"],
  "null_treatments": {
    "column_name": "treatment applied — e.g. 'binary flag created: email_optout', 'treated as zero', 'imputed with median'"
  },
  "nodes": {
    "eda": {
      "status": "complete",
      "started": "YYYY-MM-DD HH:MM",
      "completed": "YYYY-MM-DD HH:MM",
      "findings": {
        "row_count": 0,
        "column_count": 0,
        "target_variable": "column name",
        "target_distribution": {
          "group_1_label": "label from intake",
          "group_1_count": 0,
          "group_1_pct": 0.0,
          "group_2_label": "label from intake",
          "group_2_count": 0,
          "group_2_pct": 0.0
        },
        "null_flags": ["column: pct% null — treatment applied"],
        "distribution_flags": ["column: observation — e.g. right-skewed, bimodal"],
        "correlation_flags": [
          {"pair": ["col_a", "col_b"], "correlation": 0.0, "recommendation": "drop col_b"}
        ],
        "leakage_flags": ["column excluded — reason"]
      },
      "user_decisions": {
        "columns_excluded_reason": {"column_name": "reason"},
        "null_treatment_decisions": {"column_name": "treatment"}
      },
      "flags_raised": ["list of unresolved flags to carry forward"],
      "flags_resolved": ["list of flags resolved by analyst decision"]
    }
  }
}
```

**Mandatory:** `columns_retained` and `columns_excluded` at the root level of state must be fully populated before this node is marked complete. Segmentation reads `columns_retained` directly — if it is empty, segmentation will fail silently.



- Generate the HTML report first, always. The HTML report is the primary artifact — the text summary is secondary.
- Every chart must have a title, axis labels, and a fully configured `hovertemplate`. Charts with default Plotly hover labels (showing variable names like "x=..." or "y=...") are not acceptable — always write explicit business-language hover text.
- Open the HTML report automatically in the default browser after saving it using:
```python
import webbrowser, os
webbrowser.open("file://" + os.path.abspath(output_path))
```
This is cross-platform and works correctly on Mac, Linux, and Windows.
- If a chart cannot be generated due to a data issue (e.g. all nulls in a column, zero variance), skip that chart gracefully and note the skip in the text summary. Do not let one bad column break the entire report.
- Be specific in the text summary — name columns, state numbers, make recommendations. Do not hedge.
- Where a finding could have multiple explanations — behavioral, seasonal, regulatory, structural — state all plausible explanations. Do not choose between them without analyst input.
- Do not begin any segmentation or modeling — this node ends at EDA.
- If the data is fundamentally insufficient to answer the business question — wrong grain, missing key variables, excessive missingness — say so immediately in the chat panel before generating any charts.
- Save a static PNG fallback for Section 5 (target variable split distributions) only, using `fig.write_image(os.path.join(output_dir, "target_split_distributions.png"))` — this is the one chart most likely to be shared in a presentation. Requires the `kaleido` package (`pip install kaleido`).
