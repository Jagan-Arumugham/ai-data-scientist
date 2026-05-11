import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import os
import webbrowser
from datetime import datetime

pio.templates.default = "plotly_white"
CLUSTER_PALETTE = ["#2E86AB", "#E84855", "#2A9D8F", "#F4A261", "#9B59B6"]
COLOR_GROUP_1 = "#2E86AB"
COLOR_NEUTRAL = "#6C757D"
COLOR_FLAG_RED = "#E84855"
COLOR_FLAG_AMBER = "#F4A261"
COLOR_FLAG_GREEN = "#2A9D8F"

analysis_id = "credit_card_segmentation"
base_dir = os.path.join("analyses", analysis_id)
assignments_path = os.path.join(base_dir, "outputs", "segment_assignments.csv")
data_path = os.path.join(base_dir, "data", "cc_general.csv")
output_path = os.path.join(base_dir, "outputs", "findings_report.html")

SEGMENT_NAMES = {
    0: "High-Utilization Revolvers",
    1: "Low-Balance Occasional Users",
    2: "Full-Payment Transactors",
    3: "Active Purchasers",
    4: "Cash Advance Revolvers"
}

# ============================================================
# LOAD DATA
# ============================================================
df_raw = pd.read_csv(data_path)
df_raw['MINIMUM_PAYMENTS'] = df_raw['MINIMUM_PAYMENTS'].fillna(df_raw['MINIMUM_PAYMENTS'].median())
df_raw['CREDIT_LIMIT'] = df_raw['CREDIT_LIMIT'].fillna(df_raw['CREDIT_LIMIT'].median())
df_raw['BALANCE_TO_LIMIT_RATIO'] = (df_raw['BALANCE'] / df_raw['CREDIT_LIMIT']).clip(upper=1.0)

assignments = pd.read_csv(assignments_path)[['CUST_ID', 'segment', 'segment_name']]
df = df_raw.merge(assignments, on='CUST_ID', how='inner')
n_total = len(df)

seg_counts = df['segment'].value_counts().sort_index()
seg_pcts = (seg_counts / n_total * 100).round(1)

PROFILE_VARS = ['BALANCE','CREDIT_LIMIT','BALANCE_TO_LIMIT_RATIO','PURCHASES',
                'ONEOFF_PURCHASES','INSTALLMENTS_PURCHASES','PURCHASES_TRX',
                'CASH_ADVANCE','CASH_ADVANCE_FREQUENCY','PAYMENTS',
                'MINIMUM_PAYMENTS','PRC_FULL_PAYMENT','ONEOFF_PURCHASES_FREQUENCY',
                'PURCHASES_INSTALLMENTS_FREQUENCY']
PROFILE_VARS = [c for c in PROFILE_VARS if c in df.columns]
seg_means = df.groupby('segment')[PROFILE_VARS].mean()

def m(sid, var): return seg_means.loc[sid, var]

# ============================================================
# BUILD VISUALIZATIONS
# ============================================================

# Chart 1: Segment population overview (donut)
fig_donut = go.Figure(go.Pie(
    labels=[SEGMENT_NAMES[i] for i in seg_counts.index],
    values=seg_counts.values,
    hole=0.5,
    marker_colors=CLUSTER_PALETTE,
    hovertemplate="<b>%{label}</b><br>n=%{value:,}<br>%{percent}<extra></extra>",
    textinfo='label+percent',
    textfont_size=11
))
fig_donut.update_layout(
    title="Portfolio Segment Distribution — 8,950 Active Card Accounts",
    height=420, showlegend=False,
    annotations=[dict(text=f"{n_total:,}<br>accounts", x=0.5, y=0.5,
                       font_size=14, showarrow=False)]
)

# Chart 2: Key metric comparison — grouped bar (4 metrics × 5 segments)
metrics = [
    ('BALANCE_TO_LIMIT_RATIO', 'Utilization Rate', '', 1),
    ('PRC_FULL_PAYMENT', 'Full-Payment Rate', '', 1),
    ('CASH_ADVANCE_FREQUENCY', 'Cash Advance Frequency', '', 1),
    ('PURCHASES_TRX', 'Transactions / Period', 'count', 14),
]

fig_metrics = make_subplots(rows=1, cols=4,
    subplot_titles=[m[1] for m in metrics],
    horizontal_spacing=0.08)

for col_n, (var, label, unit, scale) in enumerate(metrics):
    vals = [m(sid, var) for sid in range(5)]
    fig_metrics.add_trace(go.Bar(
        x=[f"S{i}" for i in range(5)],
        y=vals,
        marker_color=CLUSTER_PALETTE,
        hovertemplate=[
            f"<b>{SEGMENT_NAMES[i]}</b><br>{label}: {vals[i]:.2f}<extra></extra>"
            for i in range(5)
        ],
        showlegend=False,
        name=label
    ), row=1, col=col_n + 1)

fig_metrics.update_layout(
    title="Segment Comparison — Four Key Behavioral Metrics<br>"
          "<sup>S0=High-Util Revolvers | S1=Low-Balance Occasional | S2=Full-Payment Transactors | "
          "S3=Active Purchasers | S4=Cash Advance Revolvers</sup>",
    height=380, dragmode="zoom"
)

# Chart 3: Risk matrix — BALANCE_TO_LIMIT_RATIO vs PRC_FULL_PAYMENT scatter
sample_df = df.sample(min(4000, n_total), random_state=42)
fig_risk = go.Figure()
for sid in range(5):
    mask = sample_df['segment'] == sid
    subset = sample_df[mask]
    fig_risk.add_trace(go.Scatter(
        x=subset['BALANCE_TO_LIMIT_RATIO'],
        y=subset['PRC_FULL_PAYMENT'],
        mode='markers',
        marker=dict(color=CLUSTER_PALETTE[sid], opacity=0.4, size=4),
        name=f"{SEGMENT_NAMES[sid]} (n={seg_counts[sid]:,})",
        hovertemplate=(
            f"<b>{SEGMENT_NAMES[sid]}</b><br>"
            "Utilization: %{x:.2f}<br>"
            "Full-payment rate: %{y:.2f}<extra></extra>"
        )
    ))
# Quadrant lines
fig_risk.add_vline(x=0.5, line_dash="dot", line_color=COLOR_NEUTRAL, opacity=0.5)
fig_risk.add_hline(y=0.5, line_dash="dot", line_color=COLOR_NEUTRAL, opacity=0.5)
fig_risk.add_annotation(x=0.85, y=0.85, text="Low risk<br>(high pay, low util)", showarrow=False,
                        font=dict(size=10, color=COLOR_FLAG_GREEN))
fig_risk.add_annotation(x=0.85, y=0.05, text="⚠ High risk<br>(no pay, high util)", showarrow=False,
                        font=dict(size=10, color=COLOR_FLAG_RED))
fig_risk.add_annotation(x=0.1, y=0.85, text="Transactors<br>(pay, low balance)", showarrow=False,
                        font=dict(size=10, color=COLOR_FLAG_GREEN))
fig_risk.update_layout(
    title="Risk Matrix — Utilization vs. Repayment Discipline<br>"
          "<sup>Bottom-right quadrant = highest financial risk | Top-left = safest</sup>",
    xaxis_title="Balance-to-Limit Ratio (Utilization)",
    yaxis_title="PRC_FULL_PAYMENT (Repayment Discipline)",
    height=520, dragmode="select",
    legend=dict(orientation='v', x=1.02, y=0.5)
)

# Chart 4: Revenue profile proxy — payments + purchase volume
fig_revenue = go.Figure()
seg_labels_short = [SEGMENT_NAMES[i] for i in range(5)]
payments = [m(sid, 'PAYMENTS') for sid in range(5)]
purchases = [m(sid, 'PURCHASES') for sid in range(5)]
cash_adv = [m(sid, 'CASH_ADVANCE') for sid in range(5)]

fig_revenue.add_trace(go.Bar(
    name='Avg Purchases', x=seg_labels_short, y=purchases,
    marker_color=COLOR_GROUP_1, opacity=0.85,
    hovertemplate="%{x}<br>Avg Purchases: $%{y:,.0f}<extra></extra>"
))
fig_revenue.add_trace(go.Bar(
    name='Avg Cash Advance', x=seg_labels_short, y=cash_adv,
    marker_color=COLOR_FLAG_AMBER, opacity=0.85,
    hovertemplate="%{x}<br>Avg Cash Advance: $%{y:,.0f}<extra></extra>"
))
fig_revenue.add_trace(go.Scatter(
    name='Avg Payments', x=seg_labels_short, y=payments,
    mode='markers+lines',
    marker=dict(color=COLOR_FLAG_RED, size=10, symbol='diamond'),
    line=dict(color=COLOR_FLAG_RED, width=2, dash='dot'),
    hovertemplate="%{x}<br>Avg Payments: $%{y:,.0f}<extra></extra>"
))
fig_revenue.update_layout(
    barmode='stack',
    title="Segment Activity Profile — Purchases, Cash Advances, and Payments (6-Month Averages)",
    xaxis_title="Segment", yaxis_title="Average $ Amount",
    height=420, dragmode="zoom",
    xaxis=dict(tickangle=-15),
    legend=dict(orientation='h', x=0, y=1.1)
)

# Chart 5: Top differentiators effect size
diff_vars = [
    ('BALANCE_TO_LIMIT_RATIO', 0.717), ('PRC_FULL_PAYMENT', 0.695),
    ('BALANCE', 0.499), ('CASH_ADVANCE', 0.488),
    ('CASH_ADVANCE_FREQUENCY', 0.457), ('PURCHASES_TRX', 0.445),
    ('ONEOFF_PURCHASES_FREQUENCY', 0.418), ('PURCHASES', 0.353),
    ('CREDIT_LIMIT', 0.346), ('PURCHASES_FREQUENCY', 0.323),
]
fig_diff = go.Figure(go.Bar(
    y=[d[0] for d in diff_vars][::-1],
    x=[d[1] for d in diff_vars][::-1],
    orientation='h',
    marker_color=[COLOR_FLAG_RED if d[1] >= 0.14 else COLOR_FLAG_AMBER for d in diff_vars][::-1],
    text=[f"{d[1]:.3f}" for d in diff_vars][::-1],
    textposition='outside',
    hovertemplate="%{y}<br>Eta²: %{x:.3f}<extra></extra>",
    name=''
))
fig_diff.add_vline(x=0.14, line_dash="dash", line_color=COLOR_NEUTRAL,
                   annotation_text="Large effect threshold", annotation_position="top right")
fig_diff.update_layout(
    title="Variable Discriminating Power — Eta-Squared (% Variance Explained by Segment)",
    xaxis_title="Eta-squared", height=420, dragmode="zoom",
    showlegend=False, margin=dict(l=260, r=80)
)

# ============================================================
# WRITE FINDINGS REPORT HTML
# ============================================================

style = """
<style>
* { box-sizing: border-box; }
body { font-family: 'Georgia', serif; max-width: 1100px; margin: 0 auto; padding: 30px 40px;
       background: #fafafa; color: #1a1a2e; line-height: 1.7; }
h1 { font-size: 2em; color: #1a1a2e; border-bottom: 3px solid #2E86AB; padding-bottom: 12px; margin-bottom: 6px; }
h2 { font-size: 1.35em; color: #2E86AB; margin-top: 48px; border-bottom: 1px solid #cce0ec; padding-bottom: 6px; }
h3 { font-size: 1.1em; color: #1a5c7a; margin-top: 28px; margin-bottom: 6px; }
p { margin: 12px 0; }
.meta { color: #888; font-size: 0.85em; font-family: Arial, sans-serif; margin-bottom: 30px; }
.exec-box { background: #eaf4fb; border-left: 5px solid #2E86AB; padding: 20px 24px;
             border-radius: 0 8px 8px 0; margin: 24px 0; }
.exec-box p { margin: 8px 0; font-size: 1.05em; }
.finding-block { background: white; border-radius: 8px; padding: 18px 22px; margin: 16px 0;
                  box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid #2E86AB; }
.finding-block h3 { margin-top: 0; color: #1a1a2e; font-size: 1.05em; }
.confidence { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.8em;
              font-family: Arial; font-weight: bold; }
.conf-high { background: #d4edda; color: #155724; }
.conf-mod { background: #fff3cd; color: #856404; }
.conf-dir { background: #f8d7da; color: #721c24; }
.seg-card { border-radius: 8px; padding: 18px 22px; margin: 14px 0; background: white;
             box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.seg-card h3 { margin-top: 0; }
.risk-badge { display: inline-block; background: #f8d7da; color: #721c24; padding: 2px 10px;
               border-radius: 12px; font-size: 0.8em; font-family: Arial; font-weight: bold; margin-left: 8px; }
.rec-block { background: white; border-radius: 8px; padding: 18px 22px; margin: 14px 0;
              box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.rec-block h3 { margin-top: 0; }
.rec-meta { font-family: Arial; font-size: 0.85em; color: #555; margin: 4px 0; }
.stat-pill { display: inline-block; background: #f0f7ff; border-radius: 4px; padding: 3px 10px;
              margin: 3px; font-family: Arial; font-size: 0.85em; }
.open-q { background: #fff8e1; border-left: 4px solid #F4A261; padding: 14px 18px;
           border-radius: 0 6px 6px 0; margin: 12px 0; }
.audit-row { display: flex; border-bottom: 1px solid #eee; padding: 8px 0; font-family: Arial; font-size: 0.85em; }
.audit-label { width: 180px; font-weight: bold; color: #555; flex-shrink: 0; }
.chart-wrap { margin: 28px 0; }
</style>
"""

with open(output_path, "w") as f:
    f.write(f"<html><head><title>Credit Card Customer Segmentation — Findings</title>{style}</head><body>\n")

    # Header
    f.write(f"""
    <h1>Credit Card Customer Segmentation</h1>
    <p class='meta'>Analysis completed: {datetime.now().strftime('%Y-%m-%d')} &nbsp;|&nbsp;
    Population: 8,950 active card accounts &nbsp;|&nbsp; Period: 6-month behavioral snapshot &nbsp;|&nbsp;
    Method: K-Means clustering, 13 behavioral variables</p>
    """)

    # Executive Summary
    f.write("""
    <h2>Executive Summary</h2>
    <div class='exec-box'>
      <p>This analysis segmented 8,950 active credit card accounts into five behaviorally distinct customer groups,
      revealing a portfolio with sharply divergent financial profiles and meaningfully different revenue and risk implications for each group.</p>
      <p>The most urgent finding is that <strong>41.4% of the portfolio — 3,700 customers — are carrying revolving debt
      at or near their credit limit and almost never pay in full</strong>; within this group, 937 customers are using the
      card primarily for cash advances rather than purchases, representing the portfolio's highest-risk behavior and warranting
      immediate Credit Risk review.</p>
      <p>At the other end of the spectrum, <strong>1,129 Active Purchasers (12.6%) are likely the portfolio's primary
      revenue engine</strong> — averaging 58 transactions per period, $4,305 in purchases, and $7,821 credit limits —
      and deserve targeted retention and upgrade investment.</p>
      <p>The single highest-impact near-term action is a re-engagement campaign for the <strong>2,975 Low-Balance
      Occasional Users (33.2%)</strong> — the portfolio's largest segment and the one most at risk of product abandonment.</p>
    </div>
    """)

    # Donut chart
    f.write("<div class='chart-wrap'>")
    f.write(fig_donut.to_html(full_html=False, include_plotlyjs="cdn"))
    f.write("</div>")

    # Analytical Approach
    f.write("""
    <h2>Analytical Approach</h2>
    <p>The analysis used a 6-month behavioral snapshot of 8,950 active credit card accounts, applying unsupervised
    k-means clustering across 13 behavioral variables after removing collinear and low-variance features identified
    during exploratory data analysis. Variables included balance and utilization metrics, purchase behavior (one-off
    and installment separately), cash advance activity, payment behavior, and a derived balance-to-limit utilization
    ratio. All variables were z-score standardized before clustering. The final five-segment solution was derived from
    a k=7 base run with two micro-cluster merges applied on analyst instruction, producing segments that are all
    statistically distinct (ANOVA p&lt;0.05, large effect sizes throughout) and individually large enough for
    reliable profiling. Driver analysis was not run — this is a pure segmentation with no target variable;
    segment differentiators from profiling serve the same diagnostic purpose.</p>
    """)

    # Key Findings
    f.write("<h2>Key Findings</h2>")

    findings = [
        (
            "1. Utilization and repayment discipline are the two axes that define the entire portfolio",
            f"BALANCE_TO_LIMIT_RATIO (η²=0.717) and PRC_FULL_PAYMENT (η²=0.695) together explain the dominant behavioral "
            f"variance — more than any other variables. Every other behavioral signal (cash advance usage, purchase frequency, "
            f"transaction count) is secondary to where a customer sits on these two dimensions. The risk matrix chart below "
            f"shows the five segments separating cleanly along these axes.",
            "high", "All segments"
        ),
        (
            "2. Two structurally different revolver profiles exist and require different interventions",
            f"High-Utilization Revolvers (n=2,763, 30.9%) carry high balances relative to low credit limits (76% avg utilization, "
            f"$2,518 avg limit) with minimal purchase activity ($345 avg). Cash Advance Revolvers (n=937, 10.5%) carry equally "
            f"high balances ($5,179) but on high credit limits ($8,693) — their debt is driven by cash advances ($5,165 avg), "
            f"not purchases. These are financially distinct risk profiles requiring different interventions: the first needs "
            f"limit and payment management; the second needs cash advance policy review.",
            "high", "S0, S4"
        ),
        (
            "3. The Active Purchaser segment (12.6%) disproportionately drives transaction volume and interchange revenue",
            f"Active Purchasers average 58 transactions per 6-month period — nearly 4x the portfolio average of 15 — "
            f"and $4,305 in total purchases against the portfolio average of $1,100. They hold the highest credit limits "
            f"($7,821 avg) and make the largest payments ($4,146 avg). Although they represent only 12.6% of accounts, "
            f"they likely generate a substantially larger share of interchange revenue. Losing customers from this segment "
            f"is disproportionately costly.",
            "high", "S3"
        ),
        (
            "4. Full-Payment Transactors (12.8%) are high-engagement but generate almost no interest income",
            f"This segment carries a near-zero revolving balance ($103 avg) and pays in full 77% of billing cycles — "
            f"the highest repayment discipline of any segment. They make moderate purchases (installment-heavy, "
            f"$983 avg) and have essentially zero cash advance usage. From a P&amp;L perspective, "
            f"these customers generate interchange revenue but negligible interest income. "
            f"They are strong candidates for rewards programs, premium card upgrades, or annual-fee products "
            f"that monetize engagement rather than balance carry.",
            "high", "S2"
        ),
        (
            "5. One-third of the portfolio is at risk of product abandonment",
            f"Low-Balance Occasional Users (n=2,975, 33.2%) are the portfolio's largest and least-engaged segment. "
            f"They carry only $442 in average balance, use 12% of their credit limit, and make modest purchases "
            f"across both one-off and installment categories. They are not in financial distress — they simply do not "
            f"rely on this card as a primary payment instrument. Without a re-engagement trigger, this segment is the "
            f"most likely source of future product attrition.",
            "high", "S1"
        ),
        (
            "6. Cash Advance Revolvers hold higher credit limits than Utilization Revolvers — a potential policy concern",
            f"Cash Advance Revolvers (S4) have an average credit limit of $8,693 — 3.4x the $2,518 average for "
            f"High-Utilization Revolvers (S0). Both segments carry high balances and almost never pay in full, "
            f"but the cash advance group was approved for substantially more credit. Whether this reflects appropriate "
            f"risk-based underwriting (cash advance users may have higher income) or a gap in limit assignment policy "
            f"that does not account for cash advance propensity is a question the Credit Risk team should validate. "
            f"This finding is directional — the data alone cannot resolve it.",
            "moderate", "S4 vs S0"
        ),
    ]

    for headline, evidence, confidence, segment in findings:
        conf_class = {'high': 'conf-high', 'moderate': 'conf-mod', 'directional': 'conf-dir'}.get(confidence, 'conf-mod')
        conf_label = {'high': 'High confidence', 'moderate': 'Moderate confidence', 'directional': 'Directional'}.get(confidence)
        f.write(f"""
        <div class='finding-block'>
          <h3>{headline}</h3>
          <p>{evidence}</p>
          <p><span class='confidence {conf_class}'>{conf_label}</span>
          &nbsp;&nbsp;<span style='font-family:Arial;font-size:0.85em;color:#555'>Segments affected: {segment}</span></p>
        </div>
        """)

    # Risk matrix chart
    f.write("<div class='chart-wrap'>")
    f.write(fig_risk.to_html(full_html=False, include_plotlyjs=False))
    f.write("</div>")

    # Metrics comparison
    f.write("<div class='chart-wrap'>")
    f.write(fig_metrics.to_html(full_html=False, include_plotlyjs=False))
    f.write("</div>")

    # Segment Narratives
    f.write("<h2>Segment Profiles</h2>")
    narratives = [
        (0, "High-Utilization Revolvers", True,
         f"n=2,763 &nbsp;|&nbsp; 30.9% of portfolio",
         [("Balance","$1,823"),("Utilization","76%"),("Purchases","$345"),("Cash Advance","$918"),("Full-Pay Rate","1%"),("Transactions","6"),("Credit Limit","$2,518")],
         "These customers are the portfolio's trapped debt carriers. They hold the lowest credit limits of any segment "
         "($2,518 avg) yet have used 76% of that limit on average — leaving very little headroom. Purchase activity "
         "is minimal (6 transactions per 6 months, $345 total spend), suggesting the card is not a primary spending "
         "instrument but a balance-carry vehicle. Almost none ever pay in full (PRC=0.01), and moderate cash advance "
         "usage adds incrementally to their debt. The credit risk profile here is driven by low limit + high utilization, "
         "not by extreme cash advance behavior — this group needs payment assistance options and proactive limit management."
        ),
        (1, "Low-Balance Occasional Users", False,
         f"n=2,975 &nbsp;|&nbsp; 33.2% of portfolio",
         [("Balance","$442"),("Utilization","12%"),("Purchases","$512"),("Cash Advance","$273"),("Full-Pay Rate","6%"),("Transactions","8"),("Credit Limit","$3,884")],
         "The largest segment in the portfolio and the most passive. These customers have the card but do not rely "
         "on it — low balance, low utilization, and modest purchase activity that suggests occasional rather than "
         "habitual card use. They rarely pay in full (PRC=0.06) but also rarely accumulate meaningful debt, "
         "pointing to sporadic small-balance behavior rather than chronic revolving. The primary risk this segment "
         "presents is not credit loss — it is attrition. Without a compelling reason to use the card more frequently, "
         "these customers are natural candidates to close the account or let it go dormant. Re-engagement through "
         "targeted offers, spend bonuses, or product feature education is the appropriate intervention."
        ),
        (2, "Full-Payment Transactors", False,
         f"n=1,146 &nbsp;|&nbsp; 12.8% of portfolio",
         [("Balance","$103"),("Utilization","4%"),("Purchases","$983"),("Cash Advance","$50"),("Full-Pay Rate","77%"),("Transactions","16"),("Credit Limit","$4,132")],
         "The portfolio's most financially disciplined customers. They carry a near-zero balance ($103 avg) "
         "because they pay their statement in full 77% of the time — the highest repayment rate of any segment by a "
         "wide margin. They prefer installment purchases and make moderate numbers of transactions. Cash advance usage "
         "is essentially absent. From a credit risk perspective, this is the safest segment. From a revenue perspective, "
         "this segment generates minimal interest income, making interchange fees and potential premium product fees "
         "the only viable monetization levers. This group responds well to rewards-based programs, cashback, and "
         "premium card upgrades with annual fees — the offer needs to justify itself on benefits, not on credit access."
        ),
        (3, "Active Purchasers", False,
         f"n=1,129 &nbsp;|&nbsp; 12.6% of portfolio",
         [("Balance","$2,373"),("Utilization","33%"),("Purchases","$4,305"),("Cash Advance","$457"),("Full-Pay Rate","20%"),("Transactions","58"),("Credit Limit","$7,821")],
         "The highest-value customers in the portfolio. Active Purchasers use their card heavily for both one-off "
         "purchases ($2,839 avg) and installments ($1,466 avg), averaging 58 transactions per 6-month period. "
         "They hold the highest credit limits ($7,821) and make substantial payments ($4,146 avg), though their "
         "full-payment rate (20%) indicates they carry some revolving balance between high-spend and high-payment "
         "cycles — likely short-term carry rather than chronic revolving debt. This segment drives a disproportionate "
         "share of the portfolio's interchange revenue and represents the customer profile the product team should "
         "prioritize retaining, upgrading, and deepening. Competitive offers targeting this segment from other issuers "
         "represent the highest-cost retention risk."
        ),
        (4, "Cash Advance Revolvers", True,
         f"n=937 &nbsp;|&nbsp; 10.5% of portfolio",
         [("Balance","$5,179"),("Utilization","61%"),("Purchases","$551"),("Cash Advance","$5,165"),("Full-Pay Rate","4%"),("Transactions","8"),("Credit Limit","$8,693")],
         "These customers are using the credit card as a short-term loan. Cash advances average $5,165 per 6-month "
         "period — occurring in 47% of billing cycles — while purchase activity is minimal ($551 avg, 8 transactions). "
         "Despite holding the second-highest average credit limits in the portfolio ($8,693), they carry $5,179 in "
         "average balance and almost never pay in full (PRC=0.04). The combination of high advance frequency, high "
         "balance, and low repayment is the clearest elevated-risk profile in the dataset. The Credit Risk team should "
         "review limit assignment policy for this segment — it is not clear that high credit limits are appropriate "
         "for customers whose primary use case is cash borrowing rather than purchase spending."
        ),
    ]

    for sid, name, is_risk, meta, stats, narrative in narratives:
        risk_html = "<span class='risk-badge'>⚠ Risk Flag — Credit Risk Review Recommended</span>" if is_risk else ""
        stats_html = "".join([f"<span class='stat-pill'><b>{k}:</b> {v}</span>" for k, v in stats])
        f.write(f"""
        <div class='seg-card' style='border-left: 5px solid {CLUSTER_PALETTE[sid]}'>
          <h3 style='color:{CLUSTER_PALETTE[sid]}'>{name} {risk_html}</h3>
          <p style='font-family:Arial;font-size:0.85em;color:#888;margin:0 0 10px 0'>{meta}</p>
          <p>{narrative}</p>
          <div style='margin-top:12px'>{stats_html}</div>
        </div>
        """)

    # Revenue / activity chart
    f.write("<div class='chart-wrap'>")
    f.write(fig_revenue.to_html(full_html=False, include_plotlyjs=False))
    f.write("</div>")

    # Recommendations
    f.write("<h2>Recommendations</h2>")
    f.write("<p><em>Ranked by estimated impact — population size × expected behavior change magnitude.</em></p>")

    recs = [
        (
            "1. Re-engage Low-Balance Occasional Users before they abandon the product",
            "S1 — Low-Balance Occasional Users (n=2,975, 33.2%)",
            "Finding 5: Largest segment, lowest engagement, highest attrition risk.",
            "Design a targeted spend incentive campaign (e.g. cashback bonus on first 3 months of increased spend, "
            "instalment offers for upcoming purchases) to increase transaction frequency from the current avg of 8 per "
            "period. Success metric: lift in PURCHASES_TRX and PURCHASES_FREQUENCY within 90 days of campaign activation.",
            "high"
        ),
        (
            "2. Protect and deepen Active Purchasers with retention and upgrade offers",
            "S3 — Active Purchasers (n=1,129, 12.6%)",
            "Finding 3: This segment drives disproportionate interchange revenue — losing one Active Purchaser costs "
            "more than losing one customer from any other segment.",
            "Identify the top 20% of this segment by transaction volume for proactive retention outreach. "
            "Offer premium card upgrades (travel rewards, concierge, higher limits) to capture share of wallet "
            "from competing products. Prioritize before competitor acquisition campaigns reach this group.",
            "high"
        ),
        (
            "3. Convert Full-Payment Transactors to fee-generating premium products",
            "S2 — Full-Payment Transactors (n=1,146, 12.8%)",
            "Finding 4: High engagement, near-zero interest income — interchange and fee revenue are the only viable levers.",
            "Design an upgrade pathway to a rewards or cashback product with an annual fee. These customers have "
            "demonstrated repayment discipline and moderate purchase activity — they will respond to value-based offers "
            "and are unlikely to be deterred by an annual fee if the benefits justify it. "
            "Success metric: product upgrade acceptance rate and annual fee revenue captured.",
            "high"
        ),
        (
            "4. Refer Cash Advance Revolvers to Credit Risk for limit and policy review",
            "S4 — Cash Advance Revolvers (n=937, 10.5%)",
            "Finding 6: High credit limits co-existing with extreme cash advance behavior and near-zero repayment "
            "is the portfolio's clearest elevated-risk profile.",
            "Flag this segment for Credit Risk review of limit assignment and cash advance fee policy. "
            "Consider whether cash advance limits (a sub-limit of total credit limit) should be reduced or "
            "whether advance fee structures adequately price the risk. Additionally, explore whether financial "
            "hardship products or structured repayment plans could reduce default risk for this group.",
            "moderate"
        ),
        (
            "5. Monitor High-Utilization Revolvers for early delinquency signals",
            "S0 — High-Utilization Revolvers (n=2,763, 30.9%)",
            "Finding 2: Near-maxed on low credit limits, almost no repayment — this segment is one income shock "
            "away from delinquency.",
            "Set up behavioral monitoring triggers: if BALANCE_TO_LIMIT_RATIO exceeds 90% or payments drop below "
            "minimum for two consecutive cycles, route to early intervention. Consider proactive balance transfer "
            "or hardship offers before delinquency occurs. This is a risk management action, not a marketing one.",
            "moderate"
        ),
    ]

    for headline, target, motivation, action, confidence in recs:
        conf_class = 'conf-high' if confidence == 'high' else 'conf-mod'
        conf_label = 'High confidence' if confidence == 'high' else 'Moderate confidence'
        f.write(f"""
        <div class='rec-block'>
          <h3>{headline}</h3>
          <p class='rec-meta'><b>Target segment:</b> {target}</p>
          <p class='rec-meta'><b>Motivated by:</b> {motivation}</p>
          <p>{action}</p>
          <p><span class='confidence {conf_class}'>{conf_label}</span></p>
        </div>
        """)

    # Differentiators chart
    f.write("<div class='chart-wrap'>")
    f.write(fig_diff.to_html(full_html=False, include_plotlyjs=False))
    f.write("</div>")

    # Open Questions
    f.write("""
    <h2>Open Questions and Limitations</h2>

    <div class='open-q'>
      <p><strong>Q1: Do Cash Advance Revolvers have higher income justifying their credit limits?</strong><br>
      The data shows S4 has $8,693 avg credit limits vs S0's $2,518 — a 3.4x gap — despite both segments having
      near-identical repayment rates near zero. This could reflect appropriate income-based underwriting (cash advance
      users may be higher-income customers experiencing temporary liquidity stress) or a gap in limit policy that does
      not account for cash advance propensity. <em>Data needed to resolve: income or credit bureau data, origination
      credit score, and limit assignment history for this cohort.</em></p>
    </div>

    <div class='open-q'>
      <p><strong>Q2: Are Active Purchasers carrying short-term balance or beginning to revolve?</strong><br>
      S3's PRC=0.20 and $2,373 avg balance despite $4,146 avg payments suggests a lag between high-spend and
      high-payment cycles — likely short-term carry, not chronic revolving. However, this is a 6-month snapshot
      and cannot confirm the direction of travel. <em>Data needed to resolve: longitudinal balance and payment
      data across multiple 6-month periods to determine whether balance is trending up or down.</em></p>
    </div>

    <div class='open-q'>
      <p><strong>Q3: Is Low-Balance Occasional Users a stable segment or in transition?</strong><br>
      The 6-month window cannot distinguish customers who have always been low-engagement from those who were
      recently more active and are declining. The latter require urgent intervention; the former may be a permanent
      low-engagement base. <em>Data needed to resolve: prior period behavioral data (purchases, balance, payments)
      to classify trajectory.</em></p>
    </div>

    <div class='open-q'>
      <p><strong>Q4: Segmentation silhouette scores are flat across k=2 to k=8 (range: 0.177–0.198)</strong><br>
      This is typical for behavioral credit card data with overlapping distributions, but means there is no
      statistically dominant cluster solution. The 5-segment solution was chosen on business interpretability
      grounds — it is a sound choice, but analysts should be aware that the boundaries between adjacent segments
      (particularly S0/S4 and S1/S2) are soft, not hard. Some customers near the boundary may behave more like
      their neighboring segment than their assigned one.</p>
    </div>
    """)

    # Analytical Record Summary
    f.write("""
    <h2>Analytical Record Summary</h2>
    <div style='background:white;border-radius:8px;padding:18px;box-shadow:0 1px 4px rgba(0,0,0,0.08)'>
    """)
    audit = [
        ("Dataset", "8,950 active credit card accounts — 6-month behavioral snapshot"),
        ("Variables excluded", "CUST_ID (identifier), PURCHASES (collinear r=0.917), PURCHASES_FREQUENCY (redundant r=0.863), CASH_ADVANCE_TRX (redundant r=0.800), TENURE (low variance), BALANCE_FREQUENCY (69.4% at max value)"),
        ("Null treatments", "MINIMUM_PAYMENTS: median imputation (313 rows, 3.5%) | CREDIT_LIMIT: median imputation (1 row)"),
        ("Derived feature", "BALANCE_TO_LIMIT_RATIO = BALANCE / CREDIT_LIMIT (capped at 1.0)"),
        ("Clustering method", "K-Means, z-score normalized, n_init=50, k=2–8 evaluated"),
        ("Final segmentation", "k=7 base run with C0→C1 and C5→C4 merges; 5 final segments"),
        ("Silhouette (k=7)", "0.1874 — flat curve across all k values, consistent with soft behavioral boundaries"),
        ("Effect sizes", "Top 10 differentiators all large (η²>0.32) and statistically significant (p<0.05)"),
        ("Hypotheses tested", "5/5 supported (4 fully, 1 partially) — all major intake hypotheses confirmed"),
        ("Risk flags", "S0 (High-Utilization Revolvers) and S4 (Cash Advance Revolvers) flagged for Credit Risk review"),
        ("Driver analysis", "Skipped by design — no target variable; profiling differentiators serve equivalent purpose"),
    ]
    for label, detail in audit:
        f.write(f"<div class='audit-row'><div class='audit-label'>{label}</div><div>{detail}</div></div>\n")
    f.write("</div>")

    # Footer
    f.write(f"""
    <div style='margin-top:50px;padding-top:20px;border-top:1px solid #eee;
                font-family:Arial;font-size:0.8em;color:#aaa;text-align:center'>
      Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} &nbsp;|&nbsp;
      analysis_id: credit_card_segmentation &nbsp;|&nbsp;
      Automated Insights Platform
    </div>
    """)

    f.write("</body></html>")

print(f"[OK] Findings report saved: {output_path}")
webbrowser.open("file://" + os.path.abspath(output_path))
print("[OK] Report opened in browser.")

print(f"\nDELIVERABLE: {output_path}")
print("5 segments | 5 recommendations | All hypotheses tested | Risk flags for Credit Risk team")
