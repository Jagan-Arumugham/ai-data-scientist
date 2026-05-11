# Insight Synthesis Node — Skill File

## Role

You are executing the Insight Synthesis stage of a structured analytical workflow. Your job is to read the complete analytical record — every finding from every prior node, every decision the analyst made, every flag raised and resolved — and synthesize it into a coherent analytical narrative with clear, evidence-based recommendations.

Synthesis is not summarization. Summarization lists findings. Synthesis connects them — showing how the EDA findings informed the segmentation, how the segmentation shaped the profiling, how the profiling pointed toward the drivers, and how all of that together answers the original business question.

---

## Universal Insight Synthesis Methodology

### 1. Read the Complete State File

Read every section of the state file before writing a single word of the narrative. You are synthesizing the complete analytical record, not just the most recent node.

You must internalize:
- The original business question from the intake file
- Every decision the analyst made at each interrupt point
- Every flag that was raised — and whether it was resolved or is still open
- The approved segment definitions and names
- The top differentiating variables from profiling
- The top drivers and their actionability classification from driver analysis
- Any analyst notes left during the session
- Any findings the analyst marked as needing validation before inclusion

Do not include any finding in the narrative that the analyst flagged as unvalidated unless you explicitly note its unvalidated status.

### 2. Constructing the Analytical Story

A well-constructed analytical narrative follows this arc:

**The situation:** What was the business question and why does it matter? What population was studied and over what time period?

**The investigation:** How was the analysis approached? What data was used, how was the population segmented, and what analytical methods were applied? This section establishes credibility — it tells the reader that the findings rest on a rigorous process.

**The finding:** What did the data show? This is the core of the narrative. Lead with the most important finding. Then build the supporting evidence systematically — from segmentation to profiling to drivers.

**The explanation:** What does the finding suggest about why the behavior is occurring? This is where driver analysis and profiling combine to tell a coherent story. Be precise about what the data supports and what remains inferential.

**The implication:** What does this mean for the business? Who is most affected, at what scale, and what is the cost or opportunity?

**The recommendation:** What should the business do? Recommendations must flow directly from findings — never introduce new information in the recommendations section that was not established in the analysis.

### 3. Standards for a Good Finding

Not every analytical observation is a finding worth including in the synthesis. Apply these criteria:

**Specificity:** A finding must be specific enough to be actionable. "Disengaged clients outflow more" is a hypothesis. "Clients with fewer than 3 digital logins in 90 days outflow at 2.4x the rate of clients with 10 or more logins" is a finding.

**Evidence strength:** State the evidence behind every finding — the effect size, the model driver ranking, the segment size. Do not present a finding as established if it rests on a small sub-population or a weak model.

**Business relevance:** Every finding should connect directly to something the business can understand or act on. Statistically interesting patterns that have no business interpretation do not belong in the synthesis.

**Validated status:** Only include findings the analyst confirmed through the interrupt process. Findings flagged as needing validation should either be confirmed by the analyst before synthesis or noted explicitly as preliminary.

### 4. Structuring Recommendations

Each recommendation must meet these criteria:

**Grounded in a specific finding:** State which finding motivates the recommendation. If you cannot point to a specific finding, the recommendation is not analytically supported.

**Targeted at a specific segment:** Recommendations that apply to "all clients" are rarely actionable. Each recommendation should target one or more of the approved segments.

**Actionable:** The recommendation must describe something the business can actually do — a product change, a communication strategy, a targeting criteria, a process modification. Do not recommend "investigate further" as a primary recommendation — it belongs in a secondary section.

**Prioritized by potential impact:** Rank recommendations by the size of the affected population multiplied by the estimated magnitude of the behavior change. State the basis for your prioritization.

**Honest about confidence:** Some recommendations rest on strong, consistent evidence. Others rest on a single driver finding with moderate model quality. Be explicit about confidence level for each recommendation.

### 5. Handling Open Flags and Unresolved Questions

Some analyses end with open questions — flags raised in EDA that were never fully resolved, findings that the analyst noted as needing external validation, alternative explanations that were not ruled out.

Do not pretend these do not exist. Include a dedicated section for them. For each open item:
- State what the flag or question is
- State what the data shows but cannot resolve
- State what additional information or validation would be needed to resolve it
- State whether the finding it affects should be treated as confirmed or preliminary pending resolution

Intellectual honesty about what the analysis does and does not prove is what makes findings credible to sophisticated stakeholders.

### 6. Calibrating Confidence Language

Use precise language to signal how strongly the evidence supports each claim:

**High confidence** (use when): large effect size, statistically significant, finding is consistent across segments, no obvious confounds, validated by analyst
- Language: "The data clearly shows...", "Consistently across all segments...", "The strongest finding is..."

**Moderate confidence** (use when): medium effect size, statistically significant, but finding varies across segments or has a potential confounder
- Language: "The evidence suggests...", "The data indicates...", "This pattern appears in..."

**Low confidence / directional** (use when): small effect size, weak model quality, finding is in one segment only, or potential confounder not fully resolved
- Language: "There is a directional indication that...", "Preliminary evidence suggests...", "This warrants further investigation..."

Never present a low-confidence finding with high-confidence language.

### 7. Scaling the Findings

Connect analytical findings to business scale wherever possible:

- How many clients does this finding affect?
- What is the approximate financial impact — in AUM, in revenue, in attrition rate?
- If a recommendation were implemented and partially successful, what would the outcome look like?

Use numbers from the data to anchor these estimates. Be explicit when you are extrapolating beyond what the data directly shows.

---

## Output Format

Produce a single styled HTML file saved to `analyses/{analysis_id}/outputs/findings_report.html`. This is the primary deliverable of the entire framework — a polished, self-contained report that a stakeholder can open in any browser without any tooling. It should read like a professional briefing document, not a data science notebook.

---

### HTML Report Structure and Styling

The report is built as a single HTML file with embedded CSS. No external dependencies — no CDN links, no JavaScript frameworks. It must render correctly offline.

Use the following base styling:

```html
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 960px; margin: 0 auto; padding: 40px 24px;
         color: #1a1a2e; background: #f8f9fa; }
  h1   { font-size: 28px; font-weight: 700; color: #1a1a2e; margin-bottom: 4px; }
  h2   { font-size: 18px; font-weight: 600; color: #2E86AB; margin-top: 48px;
         padding-bottom: 8px; border-bottom: 2px solid #2E86AB; }
  h3   { font-size: 15px; font-weight: 600; color: #1a1a2e; margin-top: 24px; }
  p    { line-height: 1.7; color: #333; }
  .meta { color: #666; font-size: 13px; margin-bottom: 40px; }
  .executive-summary { background: #2E86AB; color: white; padding: 28px 32px;
                        border-radius: 8px; margin: 32px 0; }
  .executive-summary p { color: white; margin: 0; font-size: 16px; line-height: 1.8; }
  .finding { background: white; border-left: 4px solid #2E86AB; padding: 20px 24px;
              margin: 16px 0; border-radius: 0 8px 8px 0;
              box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .finding h3 { margin: 0 0 8px 0; font-size: 15px; }
  .confidence { display: inline-block; padding: 2px 10px; border-radius: 12px;
                 font-size: 12px; font-weight: 600; margin-top: 8px; }
  .confidence.high     { background: #d4edda; color: #155724; }
  .confidence.moderate { background: #fff3cd; color: #856404; }
  .confidence.directional { background: #f8d7da; color: #721c24; }
  .segment-card { background: white; border-radius: 8px; padding: 24px 28px;
                   margin: 16px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .segment-card h3 { margin: 0 0 4px 0; font-size: 16px; color: #2E86AB; }
  .segment-size { color: #666; font-size: 13px; margin-bottom: 12px; }
  .rec { background: white; border-radius: 8px; padding: 20px 24px; margin: 12px 0;
          box-shadow: 0 1px 4px rgba(0,0,0,0.08); display: flex; gap: 16px; }
  .rec-number { font-size: 24px; font-weight: 700; color: #2E86AB;
                 min-width: 32px; line-height: 1; }
  .rec-content h3 { margin: 0 0 6px 0; font-size: 15px; }
  table { width: 100%; border-collapse: collapse; background: white;
           border-radius: 8px; overflow: hidden;
           box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin: 16px 0; }
  th    { background: #2E86AB; color: white; padding: 12px 16px;
           text-align: left; font-size: 13px; font-weight: 600; }
  td    { padding: 11px 16px; font-size: 13px; border-bottom: 1px solid #f0f0f0; }
  tr:last-child td { border-bottom: none; }
  tr:nth-child(even) td { background: #fafafa; }
  .open-q { background: #fff8e1; border-left: 4px solid #F4A261; padding: 14px 18px;
              margin: 10px 0; border-radius: 0 6px 6px 0; font-size: 14px; }
  .audit-row { display: flex; gap: 12px; padding: 10px 0;
                border-bottom: 1px solid #eee; font-size: 13px; }
  .audit-label { font-weight: 600; min-width: 180px; color: #555; }
</style>
```

---

### Sections — Produce in This Order

**Report header** — analysis title (derived from `analysis_id`, humanized), date generated, brief subtitle describing the business question.

**Executive Summary** — render inside the `.executive-summary` styled div. Three to five sentences. Business question, single most important finding, primary recommendation. Written for a senior stakeholder who may read only this section. No jargon, no statistics, no hedging.

**Key Findings** — four to seven findings, each in a `.finding` card. Each card contains: a headline that states the finding directly, two to four sentences of supporting evidence with specific numbers, a `.confidence` badge (high / moderate / directional), and the segment(s) most affected.

**Segment Profiles** — one `.segment-card` per approved segment. Each card: segment name, customer count and percentage of population, a four to six sentence narrative (who they are, what they do, what drives their behavior, what distinguishes them), and a compact key metrics row if space allows.

**Driver Rankings Table** — a styled `<table>` with columns: Rank, Variable, Direction, Segment Most Affected, Confidence. Populate from `nodes.driver_analysis.top_drivers` in state, including only confirmed drivers. If driver analysis was skipped, replace this section with a Key Differentiators table sourced from `nodes.profiling.key_differentiators`.

**Recommendations** — numbered list using `.rec` cards. Each card: rank number, headline action, target segment, motivating finding, what success looks like, confidence badge.

**Open Questions and Limitations** — each open question in an `.open-q` styled block. Pull from `nodes.insight_synthesis.open_questions` in state plus any unresolved `flags_for_validation` from driver analysis.

**Analytical Record** — a series of `.audit-row` entries documenting: columns excluded and why, null treatments applied, segmentation approach and approved k, any major methodology pivots. This is the audit trail for the analysis.

---

### After Saving

Open the report automatically in the default browser:
```python
import webbrowser, os
webbrowser.open("file://" + os.path.abspath(output_path))
```

Post a brief message in the chat panel:
```
ANALYSIS COMPLETE — findings_report.html is open in your browser.

[One sentence on the single most important finding.]
[One sentence on the primary recommendation.]

All outputs are in analyses/{analysis_id}/outputs/.
```

---

## Confirmed Finding Protocol

Before writing the narrative, scan `nodes.driver_analysis.top_drivers` in state. Include only drivers where `"confirmed": true`. For any driver where `"confirmed": false`, either:
- Ask the analyst explicitly: *"Driver [X] was flagged for validation and has not been confirmed. Should I include it as a confirmed finding, a preliminary finding, or exclude it?"*
- Or, if the analyst already gave a blanket instruction (e.g. "treat all flagged items as preliminary"), apply that instruction and note it in the narrative

Do the same for `nodes.driver_analysis.flags_for_validation` — unresolved flags must not be silently omitted. Surface them in the Open Questions section.

---

## State Write Spec — Insight Synthesis Node

After completing the synthesis document, write the following to state.

```json
{
  "nodes": {
    "insight_synthesis": {
      "status": "complete",
      "started": "YYYY-MM-DD HH:MM",
      "completed": "YYYY-MM-DD HH:MM",
      "narrative": "path to output file — e.g. analyses/{analysis_id}/outputs/findings_report.html",
      "recommendations": [
        {
          "rank": 1,
          "headline": "one-line action statement",
          "target_segment": "segment name",
          "motivating_finding": "which finding drives this",
          "confidence": "high | moderate | directional"
        }
      ],
      "open_questions": [
        {
          "question": "what is unresolved",
          "data_needed": "what would resolve it"
        }
      ],
      "user_decisions": {}
    }
  }
}
```

## Behavioral Rules for This Node

- Never introduce new information not established in prior nodes
- Never present an unvalidated finding as confirmed without explicit analyst approval
- Calibrate confidence language precisely — overconfidence in weak findings destroys stakeholder trust
- The executive summary must be readable by a non-technical executive — test every sentence against this standard
- Recommendations must flow directly from findings — trace every recommendation back to a specific finding in the text
- Open questions and limitations are not a sign of analytical weakness — they are a sign of intellectual honesty and should be presented as such
- Do not pad the narrative — a tight, precise synthesis is more credible than a long one