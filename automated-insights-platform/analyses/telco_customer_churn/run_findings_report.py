import json, os, webbrowser

analysis_id = "telco_customer_churn"
state_path  = os.path.join("analyses", analysis_id, "state.json")
output_path = os.path.join("analyses", analysis_id, "outputs", "findings_report.html")

with open(state_path) as f:
    state = json.load(f)

nodes     = state["nodes"]
decisions = state["decisions"]
eda_f     = nodes["eda"]["findings"]
prof      = nodes["profiling"]
da        = nodes["driver_analysis"]
syn       = nodes["insight_synthesis"]

# ── helpers ───────────────────────────────────────────────────────────────────
def conf_badge(level):
    cls = {"high": "high", "moderate": "moderate", "directional": "directional"}.get(level.lower(), "directional")
    return f'<span class="confidence {cls}">{level.title()} confidence</span>'

def pct_bar(pct, color="#2E86AB"):
    return (f'<div style="background:#e9ecef;border-radius:4px;height:8px;width:100%;margin-top:4px;">'
            f'<div style="background:{color};width:{min(pct,100):.1f}%;height:8px;border-radius:4px;"></div></div>')

# ══════════════════════════════════════════════════════════════════════════════
# CSS (exactly as specified in skill file)
# ══════════════════════════════════════════════════════════════════════════════
css = """
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
  .metric-chips { display: flex; gap: 16px; margin-top: 20px; flex-wrap: wrap; }
  .chip { background: rgba(255,255,255,0.2); border-radius: 6px; padding: 10px 18px; text-align: center; }
  .chip-value { font-size: 24px; font-weight: 700; }
  .chip-label { font-size: 11px; opacity: 0.85; margin-top: 2px; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px;
          font-weight: 600; margin: 2px; }
  .tag-action { background: #cce5f5; color: #1a5f7a; }
  .tag-struct { background: #e9ecef; color: #495057; }
  .metrics-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
  .metric-box { background: #f8f9fa; border-radius: 6px; padding: 10px 16px; min-width: 120px; }
  .metric-box .val { font-size: 20px; font-weight: 700; color: #2E86AB; }
  .metric-box .lbl { font-size: 11px; color: #666; margin-top: 2px; }
"""

# ══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
exec_summary = """26.5% of this telecom's customers have churned — a meaningful loss concentrated
almost entirely among a specific, identifiable profile: customers on month-to-month contracts
who are still in their first year with the company. The data clearly shows that contract structure
is the single strongest predictor of churn, with month-to-month customers churning at 42.7%
compared to just 2.8% for two-year contract holders. Fiber optic internet customers churn at
nearly twice the rate of any other service type — a pattern confirmed as a product quality
problem, not a pricing artifact. The primary recommendations are: convert new month-to-month
customers to longer-term contracts before the 12-month mark, and investigate what is driving
dissatisfaction with the Fiber optic product."""

exec_html = f"""
<div class="executive-summary">
  <p>{exec_summary}</p>
  <div class="metric-chips">
    <div class="chip"><div class="chip-value">7,043</div><div class="chip-label">Customers analysed</div></div>
    <div class="chip"><div class="chip-value">26.5%</div><div class="chip-label">Churn rate</div></div>
    <div class="chip"><div class="chip-value">0.838</div><div class="chip-label">Model AUC-ROC</div></div>
    <div class="chip"><div class="chip-value">7</div><div class="chip-label">Confirmed drivers</div></div>
    <div class="chip"><div class="chip-value">3</div><div class="chip-label">Recommendations</div></div>
  </div>
</div>
"""

# ══════════════════════════════════════════════════════════════════════════════
# KEY FINDINGS
# ══════════════════════════════════════════════════════════════════════════════
findings_data = [
    (
        "Contract type is the single strongest driver of churn",
        "Month-to-month customers churn at 42.7%, versus 11.3% on one-year contracts and 2.8% on two-year contracts. "
        "Month-to-month customers are 55% of the customer base yet account for 88.6% of all churners. "
        "Contract type has a consolidated importance score of 0.845 — the highest of any variable by a wide margin, "
        "and consistent across all three modelling methods (Decision Tree, Gradient Boosting, Logistic Regression).",
        "high", "Month-to-month customers (3,875)"
    ),
    (
        "The first 12 months are the critical churn window",
        "Customers who churn have a median tenure of just 10 months versus 38 months for retained customers — "
        "a large effect (Cohen's d = 0.85). Churn rate by tenure band: 52.9% in months 0–6, 35.9% in months 7–12, "
        "28.7% in months 13–24, falling to 9.5% by months 49–72. Customers who survive their first year are "
        "significantly less likely to leave.",
        "high", "All customers in their first 12 months (~2,186 customers)"
    ),
    (
        "Fiber optic customers churn at nearly twice the rate of any other internet service type",
        "Fiber optic customers churn at 41.9%, compared to 19.0% for DSL and 7.4% for customers with no internet. "
        "Fiber optic is 44% of the base (3,096 customers) but accounts for 69.4% of all churners. "
        "The logistic regression odds ratio is 1.97 — the highest in the model. "
        "This elevated churn is confirmed as a product quality problem, not a pricing or demographic artifact.",
        "high", "Fiber optic customers (3,096)"
    ),
    (
        "High monthly charges independently amplify churn risk",
        "Churners pay an average of $74.40/month versus $61.30 for retained customers — a $13.10 gap (21% higher). "
        "Monthly charges rank third in the consolidated driver model (score 0.613) and carry independent predictive "
        "weight beyond the Fiber optic effect. The combination of high charges and a month-to-month contract is "
        "the highest-risk profile in the data.",
        "high", "High-charge, month-to-month customers"
    ),
    (
        "Two-year contracts are a near-complete churn shield",
        "Two-year contract holders churn at just 2.8% — essentially negligible. "
        "This is not simply a tenure effect: two-year holders span a range of tenures and still show very low churn. "
        "The contract commitment itself appears to be the protective mechanism, with a consolidated driver score of 0.112.",
        "high", "Two-year contract holders (1,695)"
    ),
    (
        "31 variables tested and confirmed as non-drivers",
        "Gender, phone service, streaming services, online backup, device protection, partner and dependent status, "
        "senior citizen status, tech support, online security, and non-electronic-check payment methods all returned "
        "near-zero importance across all three models once contract type, tenure, and internet service were controlled for. "
        "Their univariate profiling differences were downstream effects of the core drivers, not independent causes.",
        "high", "All segments"
    ),
]

findings_html = "\n".join(
    f"""<div class="finding">
      <h3>{i+1}. {headline}</h3>
      <p>{evidence}</p>
      <div><strong>Segments affected:</strong> {segments}</div>
      {conf_badge(conf)}
    </div>"""
    for i, (headline, evidence, conf, segments) in enumerate(findings_data)
)

# ══════════════════════════════════════════════════════════════════════════════
# SEGMENT PROFILES
# ══════════════════════════════════════════════════════════════════════════════
seg_colors = {"Churned": "#E84855", "Retained": "#2E86AB"}
seg_metrics = {
    "Churned": [("1,869", "Customers"), ("26.5%", "Of base"), ("10 mo", "Median tenure"), ("$74.40", "Avg monthly charges")],
    "Retained": [("5,174", "Customers"), ("73.5%", "Of base"), ("38 mo", "Median tenure"), ("$61.30", "Avg monthly charges")],
}

segments_html = ""
for seg, narrative in prof["segment_narratives"].items():
    color = seg_colors.get(seg, "#2E86AB")
    count, pct = ("1,869", "26.5%") if seg == "Churned" else ("5,174", "73.5%")
    metrics_html = "".join(
        f'<div class="metric-box"><div class="val" style="color:{color};">{v}</div><div class="lbl">{l}</div></div>'
        for v, l in seg_metrics.get(seg, [])
    )
    segments_html += f"""
    <div class="segment-card" style="border-top: 4px solid {color};">
      <h3 style="color:{color};">{seg}</h3>
      <div class="segment-size">{count} customers &nbsp;·&nbsp; {pct} of base</div>
      <p>{narrative}</p>
      <div class="metrics-row">{metrics_html}</div>
    </div>"""

# ══════════════════════════════════════════════════════════════════════════════
# DRIVER RANKINGS TABLE
# ══════════════════════════════════════════════════════════════════════════════
confirmed_drivers = [d for d in da["top_drivers"] if d.get("confirmed")]

driver_rows = ""
for d in confirmed_drivers:
    action_tag = ('<span class="tag tag-action">Actionable</span>' if d["actionable"]
                  else '<span class="tag tag-struct">Structural</span>')
    score_bar = pct_bar(d["importance_score"] * 100, "#2E86AB" if d["actionable"] else "#6C757D")
    driver_rows += f"""<tr>
      <td><strong>{d['rank']}</strong></td>
      <td><strong>{d['variable']}</strong>
          {score_bar}
          <span style="font-size:11px;color:#888;">{d['importance_score']:.3f}</span></td>
      <td style="font-size:12px;color:#444;">{d['direction']}</td>
      <td>{action_tag}</td>
    </tr>"""

drivers_html = f"""
<p style="color:#555;font-size:13px;margin-bottom:12px;">
  Three models run: Decision Tree (AUC 0.830), Gradient Boosting (AUC 0.838),
  Logistic Regression (AUC 0.839). Rankings are consolidated across all three.
  <strong style="color:#155724;">Model quality: Reliable (AUC &gt; 0.83).</strong>
</p>
<table>
  <thead><tr>
    <th style="width:40px;">Rank</th>
    <th>Variable</th>
    <th>Direction of Effect</th>
    <th style="width:120px;">Type</th>
  </tr></thead>
  <tbody>{driver_rows}</tbody>
</table>"""

# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
recs_data = [
    (
        "Launch a contract commitment programme targeting new month-to-month customers in months 1–6",
        "Month-to-month customers, tenure 0–6 months",
        "Contract type is the #1 driver (score 0.845); 52.9% of customers churn in months 0–6; "
        "two-year contracts churn at only 2.8%.",
        "Structured outreach at months 1, 3, and 5 offering incentives — discounted rates, service credits, "
        "or bundled add-ons — in exchange for committing to a 1- or 2-year contract.",
        "A measurable reduction in 0–12 month churn in the targeted cohort versus a control group not offered the programme.",
        "high"
    ),
    (
        "Investigate and remediate the Fiber optic product experience",
        "All Fiber optic customers (3,096 — 44% of base)",
        "Fiber optic odds ratio 1.97 in logistic regression; churn rate 41.9%; "
        "confirmed as a product quality problem, not pricing or demographics.",
        "Structured review of NPS scores, complaint logs, service interruption records, and technician call rates "
        "segmented by churn status, to identify whether the failure is reliability, support quality, or feature gaps.",
        "Identification of the specific product failure point, followed by a targeted service improvement with "
        "Fiber churn rate as the primary outcome metric.",
        "high"
    ),
    (
        "Design a value reinforcement programme for high-charge month-to-month customers in their first year",
        "Month-to-month customers paying above $70/month, tenure 0–12 months",
        "MonthlyCharges ranks third as a driver (score 0.613); churners pay $13.10/month more than retained customers.",
        "Proactive value communication — usage summaries, feature discovery prompts, or personalised service reviews — "
        "to anchor perceived value before the cancellation decision. Coordinate with Fiber remediation for those on Fiber.",
        "Reduction in 0–12 month churn among the high-charge cohort, measured separately from the contract "
        "commitment programme effect.",
        "moderate"
    ),
]

recs_html = ""
for i, (headline, segment, finding, action, success, conf) in enumerate(recs_data):
    recs_html += f"""
    <div class="rec">
      <div class="rec-number">{i+1}</div>
      <div class="rec-content">
        <h3>{headline}</h3>
        <p style="margin:0 0 10px 0;font-size:13px;">{action}</p>
        <table style="box-shadow:none;margin:0;background:#f8f9fa;border-radius:6px;">
          <tr><td style="font-weight:600;color:#555;width:170px;background:transparent;">Target segment</td>
              <td style="background:transparent;">{segment}</td></tr>
          <tr><td style="font-weight:600;color:#555;background:transparent;">Motivating finding</td>
              <td style="background:transparent;">{finding}</td></tr>
          <tr><td style="font-weight:600;color:#555;background:transparent;">Success looks like</td>
              <td style="background:transparent;">{success}</td></tr>
        </table>
        {conf_badge(conf)}
      </div>
    </div>"""

# ══════════════════════════════════════════════════════════════════════════════
# OPEN QUESTIONS
# ══════════════════════════════════════════════════════════════════════════════
oqs = syn.get("open_questions", [])
oq_html = "\n".join(
    f"""<div class="open-q">
      <strong>{oq['question']}</strong><br>
      <span style="color:#666;font-size:13px;">Data needed: {oq['data_needed']}</span>
    </div>"""
    for oq in oqs
)
oq_html += """
<div class="open-q">
  <strong>Do non-driver variables matter within specific sub-segments?</strong><br>
  <span style="color:#666;font-size:13px;">Data needed: Sub-segment analysis within Fiber optic or early-tenure cohorts —
  tech support, online security, and senior citizen status may be meaningful within those groups even though
  they are non-drivers at the population level.</span>
</div>"""

# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICAL RECORD
# ══════════════════════════════════════════════════════════════════════════════
audit_html = "\n".join(
    f"""<div class="audit-row">
      <div class="audit-label">{d['node'].upper()} — {d['decision_type'].replace('_',' ').title()}</div>
      <div>{d['detail']}</div>
    </div>"""
    for d in decisions
)

# ══════════════════════════════════════════════════════════════════════════════
# ASSEMBLE FINAL HTML
# ══════════════════════════════════════════════════════════════════════════════
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Telco Customer Churn — Findings Report</title>
  <style>{css}</style>
</head>
<body>

  <h1>Telco Customer Churn — Findings Report</h1>
  <p class="meta">
    Analysis ID: {analysis_id} &nbsp;·&nbsp; Date: 2026-05-10 &nbsp;·&nbsp;
    Business question: Why are customers leaving and who is most at risk? &nbsp;·&nbsp;
    All findings analyst-confirmed
  </p>

  {exec_html}

  <h2>Key Findings</h2>
  {findings_html}

  <h2>Segment Profiles</h2>
  {segments_html}

  <h2>Driver Rankings</h2>
  {drivers_html}

  <h2>Recommendations</h2>
  {recs_html}

  <h2>Open Questions and Limitations</h2>
  {oq_html}

  <h2>Analytical Record</h2>
  <p style="font-size:13px;color:#666;margin-bottom:12px;">
    Complete log of decisions made during the analysis. All decisions were confirmed by the analyst
    before the next node proceeded.
  </p>
  {audit_html}

</body>
</html>"""

with open(output_path, "w") as f:
    f.write(html)

print(f"Saved: {output_path}")
webbrowser.open("file://" + os.path.abspath(output_path))
print("Opened in browser.")
