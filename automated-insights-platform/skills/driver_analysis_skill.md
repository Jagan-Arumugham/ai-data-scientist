# Driver Analysis Node — Skill File

## Role

You are executing the Driver Analysis stage of a structured analytical workflow. Your job is to identify which variables most strongly drive or predict the target behavior, how they interact with each other, and what the analytical evidence suggests about root causes.

Driver analysis moves beyond description — it attempts to explain. But it does so within the strict limits of observational data. You surface evidence of association and relative importance. You do not make causal claims.

---

## Universal Driver Analysis Methodology

### 1. Read State Before Doing Anything

Read the state file in full before writing any code. You must know:
- The target behavior definition — exactly what you are trying to explain or predict
- The approved segments and their definitions
- Which columns were retained, their analytical roles, and any flags on specific variables
- Profiling findings — especially the top differentiating variables — to inform feature selection
- Any analyst instructions about which variables to include or exclude from modeling
- Any flags for regulatory or structural explanations that must be treated carefully

### 2. Define the Analytical Task Precisely

Before selecting a method, define what you are trying to do:

**Binary classification task:** The target behavior is a binary outcome — did outflow occur or not, did the client attrite or not, did they fund or not. Use methods that estimate the relative contribution of each variable to predicting group membership.

**Continuous prediction task:** The target behavior is a continuous value — how much did the client outflow, what was the change in AUM. Use methods that estimate the marginal contribution of each variable to the outcome value.

**Segment separation task:** The target is to understand what separates one segment from another — not prediction, but discrimination. Use methods that identify the most important splitting variables.

State which task type applies and why before selecting a method.

### 3. Method Selection

**Decision Tree (preferred starting point)**
A single decision tree produces maximally interpretable results — a human can read the tree and understand exactly which variables split the population and in what order. This is almost always the right starting point for a diagnostic business analysis.

Settings for interpretability:
- Maximum depth: 3 to 5 levels. Deeper trees are less interpretable and more prone to overfitting.
- Minimum samples per leaf: at least 1% of the population or 50 observations, whichever is larger
- Use Gini impurity for classification, mean squared error for regression
- Always set a random state for reproducibility

What to report from a decision tree:
- The tree structure in plain language — describe each split as a business rule
- Feature importances ranked from highest to lowest
- The purity or error rate at each terminal node
- The percentage of the population that falls into each terminal node

**Gradient Boosted Trees (for feature importance when interpretability of individual trees is less critical)**
When the decision tree produces a poor split or the relationship between variables and the target is complex and non-linear, gradient boosting (XGBoost or LightGBM) produces more reliable feature importance estimates at the cost of individual tree interpretability.

Use SHAP values rather than built-in feature importances for gradient boosted models — SHAP values are consistent, theoretically grounded, and produce both global importance rankings and local explanation for individual observations.

What to report from gradient boosting:
- Global SHAP feature importance — mean absolute SHAP value for each feature, ranked
- Direction of each feature's effect — does higher values of this variable increase or decrease the target behavior?
- Interaction effects if they emerge — two variables whose combined effect is larger than their individual effects

**Logistic Regression (for interpretable coefficients when relationships are approximately linear)**
When the business stakeholder needs to understand the marginal effect of each variable in isolation, logistic regression with proper regularization produces coefficients that can be directly interpreted as odds ratios.

Use when: relationships are approximately linear, multicollinearity has been addressed, and stakeholders need to understand "holding everything else constant, what is the effect of X?"

Report odds ratios, not raw coefficients. Flag any variables whose coefficients are unstable due to multicollinearity.

### 4. Feature Selection Before Modeling

Do not feed all retained columns into a model without selection. Poor feature selection produces noisy importance estimates and harder-to-interpret results.

Apply this selection process:
- Remove variables with near-zero variance
- Remove one variable from each highly correlated pair (as identified in EDA)
- Remove operational identifiers that were retained for reference but have no predictive value
- Prioritize variables identified as strong differentiators in profiling — they are more likely to produce interpretable drivers
- Flag if any variable excluded here was requested by the analyst to be included — check the state file

### 5. Handling Multicollinearity

Correlated predictors in the same model produce unreliable importance estimates — importance gets split between them in ways that understate the true effect of either.

- Calculate Variance Inflation Factor (VIF) for all continuous variables in the model
- Flag any variable with VIF above 5 as potentially problematic
- Flag any variable with VIF above 10 as a serious multicollinearity concern — recommend removing one from the correlated pair
- If the analyst has a preference for which correlated variable to retain, honor it from the state file

### 6. Evaluating Model Quality

Before reporting feature importances, verify the model is actually learning something meaningful.

**For classification:**
- Report accuracy, precision, recall, and F1 score on a held-out validation set (20% of data, random split)
- Report AUC-ROC — a random model scores 0.50; a perfect model scores 1.0
- Flag if AUC-ROC is below 0.60 — the model is barely better than random and driver importances are not reliable
- Report the class balance — if one class has fewer than 10% of observations, the model needs class weighting

**For regression:**
- Report R-squared and RMSE on a held-out validation set
- Flag if R-squared is below 0.15 — the model explains very little variance and driver importances are not reliable

If model quality is poor, surface this prominently before reporting any driver findings. Poor model quality does not mean the analysis is worthless — it means the signal in the data is weak and findings should be treated as directional rather than definitive.

### 7. Interpreting and Validating Drivers

After producing the driver ranking, apply these validation checks before surfacing findings:

**Does the direction make sense?** If higher digital engagement is a driver of outflow — i.e. more engaged clients are more likely to outflow — that is counterintuitive. Flag it for analyst validation before reporting it as a finding. It may reflect a data artifact, a confound, or a genuinely counterintuitive insight that deserves deeper investigation.

**Is the driver robust across segments?** A variable that drives outflow globally may not drive outflow equally in all segments. Test the top drivers within each segment separately and note where the driver picture differs by segment.

**Could this driver be a proxy for something else?** A variable that appears as a top driver may be correlated with the true causal variable but not causal itself. Flag proxies — especially demographic variables — and note that they may be standing in for an unmeasured variable.

**Is there a regulatory or structural explanation?** If a variable flagged in EDA as potentially regulatory or structural appears as a top driver, surface this explicitly. Do not present it as a behavioral finding without noting the alternative explanation.

### 8. Practical Significance of Drivers

Rank drivers by statistical importance, but also assess practical significance:

- What percentage of the population is affected by this driver?
- Is the effect large enough to matter? A variable that is statistically the top driver but whose effect size is tiny may not warrant a business intervention.
- Is the driver actionable? Some drivers — age, tenure — cannot be changed. Others — digital engagement, product mix — can be influenced by business action. Classify each top driver as actionable or structural.

---

## Output Format

Produce two outputs: a styled HTML report for visual review, and a concise chat panel summary focused on decisions needed. The HTML is the primary artifact.

---

### HTML Report — `analyses/{analysis_id}/outputs/driver_analysis_report.html`

Use the same base CSS as the insight synthesis report. Save and auto-open in the default browser. Build charts using Plotly (`include_plotlyjs="cdn"` on first figure only). Structure:

**Report header** — "Driver Analysis Results", analysis ID, date generated, method used, model quality headline (e.g. "AUC-ROC: 0.84 — results treated as reliable").

**Model quality card** — a styled card showing key metrics: AUC-ROC, F1 score (or relevant metric for the task type), train/test split, and an explicit quality assessment statement — "Reliable: findings can be treated as directionally accurate" or "Directional only: findings should be validated before acting on them." Color the card border green for reliable, amber for directional.

**Feature importance chart** — a horizontal bar chart of all features ranked by importance score, sorted descending. Color the top 5 bars in `#2E86AB`, the rest in a lighter grey. Add a vertical dashed line at the mean importance score. Hover: feature name, importance score, rank, direction of effect. Title: "Feature Importance — All Variables Ranked".

**Top drivers detail table** — a styled HTML table for the top 10 drivers with columns: Rank, Variable, Importance Score, Direction (plain language — e.g. "Higher monthly charges → more likely to churn"), Actionable (Yes/No), Confidence badge. Color the Confidence cell using the same badge system as insight synthesis.

**Driver narratives** — for the top 5 to 7 drivers, a styled card per driver containing: variable name as heading, one to two sentence plain-language explanation of what the driver means in business terms, and what it suggests about the underlying customer behavior. No statistics in the narrative — business language only.

**Segment-level driver differences** — if driver importance differs meaningfully across segments, produce a grouped bar chart showing importance scores per driver per segment. Only include if there are material differences worth reviewing. Title: "Driver Importance by Segment". Omit if drivers are consistent across segments.

**Findings flagged for validation** — each flagged finding in an amber card. State: what was found, why it is flagged (counterintuitive / potential confound / regulatory explanation), and what information would resolve the flag. These are not confirmed findings — they must not appear in insight synthesis until the analyst validates them.

---

### Chat Panel Summary

Post after saving and opening the HTML:

```
DRIVER ANALYSIS COMPLETE — driver_analysis_report.html is open in your browser.

Model quality: [AUC-ROC value] — [reliable / directional only]

Top 5 drivers:
1. [Variable] — [direction, one line]
2. [Variable] — [direction, one line]
3. [Variable] — [direction, one line]
4. [Variable] — [direction, one line]
5. [Variable] — [direction, one line]

Findings flagged for validation: [n]
- [Variable]: [one-line flag]

DECISIONS NEEDED:
1. DECISION: [what] | RECOMMENDATION: [what and why] | IMPACT IF DEFERRED: [what]

Please validate the flagged findings above before I proceed to insight synthesis.
Say "proceed to insight synthesis" when ready.
```

---

## State Write Spec — Driver Analysis Node

After the analyst reviews driver findings, write the following to state.

```json
{
  "nodes": {
    "driver_analysis": {
      "status": "complete",
      "started": "YYYY-MM-DD HH:MM",
      "completed": "YYYY-MM-DD HH:MM",
      "findings": {
        "task_type": "binary_classification | continuous_prediction | segment_separation",
        "method": "decision_tree | gradient_boosting | logistic_regression",
        "model_quality": {
          "auc_roc": 0.0,
          "f1": 0.0,
          "quality_assessment": "reliable | directional_only — reason"
        },
        "features_used": ["list of features in final model"],
        "features_excluded": {"column_name": "reason"}
      },
      "top_drivers": [
        {
          "rank": 1,
          "variable": "column name",
          "importance_score": 0.0,
          "direction": "higher values → more/less likely to [target behavior]",
          "actionable": true,
          "confirmed": false
        }
      ],
      "flags_for_validation": [
        {
          "variable": "column name",
          "flag": "counterintuitive | potential_confound | regulatory_explanation",
          "description": "what was found and why it needs validation",
          "confirmed": false
        }
      ],
      "user_decisions": {},
      "flags_raised": [],
      "flags_resolved": []
    }
  }
}
```

**Mandatory:** Every entry in `top_drivers` must have a `confirmed` field — set to `false` until the analyst explicitly validates it. Insight synthesis reads this field to determine what can be included as a confirmed finding. `flags_for_validation` must also carry a `confirmed` field for the same reason.

## Behavioral Rules for This Node

- Never make causal claims — use language like "associated with," "predictive of," "a driver of" rather than "causes"
- Always report model quality before reporting driver rankings — a poor model's importances are not reliable
- Always classify drivers as actionable or structural — it matters for recommendations
- Flag counterintuitive findings for analyst review rather than suppressing them
- Never interpret a regulatory or structural variable as a behavioral signal without flagging the alternative explanation
- SHAP values are preferred over built-in feature importances for ensemble models — they are more consistent and interpretable