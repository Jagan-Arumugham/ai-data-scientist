import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import os
import webbrowser
from datetime import datetime
from scipy import stats
from itertools import combinations

try:
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

pio.templates.default = "plotly_white"
COLOR_GROUP_1 = "#2E86AB"
COLOR_GROUP_2 = "#E84855"
COLOR_NEUTRAL = "#6C757D"
COLOR_FLAG_AMBER = "#F4A261"
COLOR_FLAG_GREEN = "#2A9D8F"
CLUSTER_PALETTE = ["#2E86AB", "#E84855", "#2A9D8F", "#F4A261", "#9B59B6"]

SEGMENT_NAMES = {
    0: "High-Utilization Revolvers",
    1: "Low-Balance Occasional Users",
    2: "Full-Payment Transactors",
    3: "Active Purchasers",
    4: "Cash Advance Revolvers"
}
N_SEGS = 5

analysis_id = "credit_card_segmentation"
base_dir = os.path.join("analyses", analysis_id)
data_path = os.path.join(base_dir, "data", "cc_general.csv")
assignments_path = os.path.join(base_dir, "outputs", "segment_assignments.csv")
output_dir = os.path.join(base_dir, "outputs")
output_path = os.path.join(output_dir, "profiling_report.html")

# ============================================================
# LOAD DATA + MERGE SEGMENT ASSIGNMENTS
# ============================================================
df_raw = pd.read_csv(data_path)
df_raw['MINIMUM_PAYMENTS'] = df_raw['MINIMUM_PAYMENTS'].fillna(df_raw['MINIMUM_PAYMENTS'].median())
df_raw['CREDIT_LIMIT'] = df_raw['CREDIT_LIMIT'].fillna(df_raw['CREDIT_LIMIT'].median())
df_raw['BALANCE_TO_LIMIT_RATIO'] = (df_raw['BALANCE'] / df_raw['CREDIT_LIMIT']).clip(upper=1.0)

assignments = pd.read_csv(assignments_path)[['CUST_ID', 'segment', 'segment_name']]
df = df_raw.merge(assignments, on='CUST_ID', how='inner')
n_rows = len(df)

# All variables to profile (include excluded-from-clustering as context)
PROFILE_VARS = [
    'BALANCE', 'CREDIT_LIMIT', 'BALANCE_TO_LIMIT_RATIO',
    'PURCHASES', 'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES', 'PURCHASES_TRX',
    'CASH_ADVANCE', 'CASH_ADVANCE_FREQUENCY',
    'PAYMENTS', 'MINIMUM_PAYMENTS', 'PRC_FULL_PAYMENT',
    'BALANCE_FREQUENCY', 'PURCHASES_FREQUENCY',
    'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
    'TENURE'
]
PROFILE_VARS = [c for c in PROFILE_VARS if c in df.columns]

seg_labels = [SEGMENT_NAMES[i] for i in range(N_SEGS)]
seg_counts = df['segment'].value_counts().sort_index()
seg_pcts = (seg_counts / n_rows * 100).round(1)

# ============================================================
# COMPUTE PER-SEGMENT STATISTICS
# ============================================================
pop_stats = {}
seg_stats = {i: {} for i in range(N_SEGS)}

for var in PROFILE_VARS:
    vals_all = df[var].dropna()
    pop_stats[var] = {
        'mean': vals_all.mean(), 'median': vals_all.median(),
        'std': vals_all.std(), 'p25': vals_all.quantile(0.25),
        'p75': vals_all.quantile(0.75)
    }
    for sid in range(N_SEGS):
        vals = df[df['segment'] == sid][var].dropna()
        seg_stats[sid][var] = {
            'mean': vals.mean(), 'median': vals.median(),
            'std': vals.std(), 'p25': vals.quantile(0.25),
            'p75': vals.quantile(0.75), 'n': len(vals)
        }

# ============================================================
# EFFECT SIZE: ETA-SQUARED FROM ONE-WAY ANOVA
# Also max pairwise Cohen's d for top variable annotation
# ============================================================
effect_sizes = {}
anova_pvals = {}
for var in PROFILE_VARS:
    groups = [df[df['segment'] == sid][var].dropna().values for sid in range(N_SEGS)]
    groups = [g for g in groups if len(g) > 1]
    if len(groups) < 2:
        effect_sizes[var] = 0.0
        anova_pvals[var] = 1.0
        continue
    f_stat, p_val = stats.f_oneway(*groups)
    anova_pvals[var] = p_val

    # Eta-squared
    all_vals = np.concatenate(groups)
    grand_mean = all_vals.mean()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_total = sum((v - grand_mean) ** 2 for v in all_vals)
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
    effect_sizes[var] = round(eta_sq, 4)

# Rank variables by effect size
ranked_vars = sorted(effect_sizes.items(), key=lambda x: x[1], reverse=True)

# Max pairwise Cohen's d for top variables
def cohens_d(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0
    pooled_std = np.sqrt(((na - 1) * a.std() ** 2 + (nb - 1) * b.std() ** 2) / (na + nb - 2))
    return abs(a.mean() - b.mean()) / pooled_std if pooled_std > 0 else 0.0

top_vars = [v for v, _ in ranked_vars[:15]]
max_cohens_d = {}
for var in top_vars:
    max_d = 0.0
    best_pair = (0, 1)
    for s1, s2 in combinations(range(N_SEGS), 2):
        a = df[df['segment'] == s1][var].dropna().values
        b = df[df['segment'] == s2][var].dropna().values
        d = cohens_d(a, b)
        if d > max_d:
            max_d = d
            best_pair = (s1, s2)
    max_cohens_d[var] = {'d': round(max_d, 3), 'pair': best_pair}

# ============================================================
# TUKEY HSD FOR TOP 8 VARIABLES
# ============================================================
tukey_results = {}
if HAS_STATSMODELS:
    for var in top_vars[:8]:
        try:
            vals = df[var].dropna()
            seg_col = df.loc[vals.index, 'segment_name']
            tukey = pairwise_tukeyhsd(vals, seg_col, alpha=0.05)
            tukey_results[var] = tukey
        except Exception:
            pass

# ============================================================
# SEGMENT NARRATIVES (data-driven drafts)
# ============================================================
NARRATIVES = {
    0: (
        "High-Utilization Revolvers are the portfolio's highest credit-risk segment. "
        "They carry balances at 76% of their credit line on average — the lowest credit limits of any segment ($2,518) "
        "yet among the highest balances relative to that limit. They make very few purchases (avg 6 transactions per period) "
        "and almost never pay their balance in full (PRC=0.01). Moderate cash advance usage adds further to their debt load. "
        "These customers are not actively disengaged — they are using the card, but primarily to carry revolving debt they are not paying down."
    ),
    1: (
        "Low-Balance Occasional Users are the portfolio's lowest-engagement segment. "
        "They carry minimal balances ($442 avg), use only 12% of their available credit, "
        "and make modest purchases across both one-off and installment categories. "
        "They rarely pay in full (PRC=0.06) but also rarely accumulate significant debt. "
        "This segment represents dormant-risk customers: they have the card but it is not their primary payment instrument. "
        "Without re-engagement, this group is at the highest risk of product abandonment or attrition."
    ),
    2: (
        "Full-Payment Transactors are the portfolio's most financially disciplined segment. "
        "They carry virtually no revolving balance ($103 avg) and pay in full 77% of billing cycles — "
        "by far the highest repayment rate in the portfolio. They favor installment purchases and make a moderate number of transactions. "
        "Almost zero cash advance usage. From a revenue standpoint, this segment generates almost no interest income, "
        "making them ideal candidates for rewards, cashback, or premium card upgrade programs that monetize through interchange and fee revenue instead."
    ),
    3: (
        "Active Purchasers are the portfolio's most valuable and engaged customers. "
        "They hold the highest credit limits ($7,821 avg), spend heavily on both one-off ($2,839) and installment ($1,466) purchases, "
        "and average 58 transactions per 6-month period — nearly 4x the portfolio average. "
        "They make substantial payments ($4,146 avg) and maintain a moderate but not alarming utilization rate (33%). "
        "This segment likely includes high-income professionals and frequent card users who drive the bulk of the portfolio's transaction volume and interchange revenue."
    ),
    4: (
        "Cash Advance Revolvers are using the credit card primarily as a short-term loan, not a purchase instrument. "
        "Their average cash advance is $5,165 per period — the highest of any segment — with cash advances occurring in 47% of billing cycles. "
        "Purchase activity is minimal (7.8 transactions). Despite having higher credit limits than most segments ($8,693), "
        "they carry high revolving balances ($5,179) and almost never pay in full (PRC=0.04). "
        "The combination of high cash advance frequency and high revolving balance represents the clearest risk profile in the dataset "
        "and warrants direct attention from the Credit Risk team."
    )
}

# ============================================================
# BUILD HTML REPORT
# ============================================================
sections = []

# --- Section 1: Top Differentiating Variables ---
top15 = ranked_vars[:15]
var_names = [v for v, _ in top15]
eta_vals = [e for _, e in top15]
sig_flags = [anova_pvals.get(v, 1.0) < 0.05 for v in var_names]

bar_colors = [COLOR_FLAG_GREEN if sig else COLOR_FLAG_AMBER for sig in sig_flags]

def eta_label(e):
    if e >= 0.14: return "Large"
    elif e >= 0.06: return "Medium"
    elif e >= 0.01: return "Small"
    else: return "Negligible"

hover_texts = []
for v, e in top15:
    sig = "Yes (p<0.05)" if anova_pvals.get(v, 1.0) < 0.05 else "No"
    cd = max_cohens_d.get(v, {})
    pair = cd.get('pair', (0, 1))
    hover_texts.append(
        f"<b>{v}</b><br>Eta-squared: {e:.4f} ({eta_label(e)})<br>"
        f"ANOVA significant: {sig}<br>"
        f"Max Cohen's d: {cd.get('d', 0):.2f} "
        f"({SEGMENT_NAMES[pair[0]][:12]} vs {SEGMENT_NAMES[pair[1]][:12]})"
    )

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    y=var_names[::-1], x=eta_vals[::-1],
    orientation='h',
    marker_color=bar_colors[::-1],
    text=[f"{e:.3f} — {eta_label(e)}" for e in eta_vals[::-1]],
    textposition='outside',
    hovertemplate=[f"{h}<extra></extra>" for h in hover_texts[::-1]],
    name=''
))
fig1.add_vline(x=0.14, line_dash="dash", line_color=COLOR_FLAG_AMBER,
               annotation_text="Large effect (0.14)", annotation_position="top right")
fig1.add_vline(x=0.06, line_dash="dot", line_color=COLOR_NEUTRAL,
               annotation_text="Medium (0.06)", annotation_position="bottom right")
fig1.update_layout(
    title="Top Differentiating Variables — Eta-Squared (Variance Explained by Segment)<br>"
          "<sup>Green = statistically significant (p<0.05) | Amber = not significant</sup>",
    xaxis_title="Eta-squared", yaxis_title="",
    height=520, dragmode="zoom", showlegend=False,
    margin=dict(l=280, r=120)
)
sections.append(("fig", "Section 1 — Top Differentiating Variables (Effect Size Ranking)", fig1))

# --- Section 2: Standardized Means Radar Chart ---
# Top 8 variables by effect size for radar
radar_vars = [v for v, _ in ranked_vars[:8]]
from sklearn.preprocessing import MinMaxScaler
radar_data = df.groupby('segment')[radar_vars].mean()
mms = MinMaxScaler()
radar_norm = pd.DataFrame(mms.fit_transform(radar_data), columns=radar_vars, index=radar_data.index)

fig2 = go.Figure()
for sid in range(N_SEGS):
    vals = radar_norm.loc[sid].tolist()
    vals.append(vals[0])  # close polygon
    fig2.add_trace(go.Scatterpolar(
        r=vals,
        theta=radar_vars + [radar_vars[0]],
        name=f"{SEGMENT_NAMES[sid]} (n={seg_counts[sid]:,})",
        line=dict(color=CLUSTER_PALETTE[sid], width=2),
        fill='toself', fillcolor=CLUSTER_PALETTE[sid],
        opacity=0.15,
        hovertemplate=f"<b>{SEGMENT_NAMES[sid]}</b><br>%{{theta}}: %{{r:.2f}}<extra></extra>"
    ))
fig2.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
    title="Segment Radar Chart — Top 8 Differentiating Variables<br>"
          "<sup>Values min-max normalised to 0-1 for comparability</sup>",
    height=560, showlegend=True,
    legend=dict(orientation='v', x=1.1, y=0.5)
)
sections.append(("fig", "Section 2 — Segment Radar Chart", fig2))

# --- Section 3: Per-Segment Mean vs Population (top 6 vars) ---
top6 = [v for v, _ in ranked_vars[:6]]
fig3_rows = 2
fig3_cols = 3
fig3 = make_subplots(rows=fig3_rows, cols=fig3_cols,
                      subplot_titles=top6,
                      horizontal_spacing=0.1, vertical_spacing=0.15)

for idx, var in enumerate(top6):
    row, col = idx // fig3_cols + 1, idx % fig3_cols + 1
    seg_means_var = [seg_stats[sid][var]['mean'] for sid in range(N_SEGS)]
    pop_mean = pop_stats[var]['mean']

    fig3.add_trace(go.Bar(
        x=[f"S{i}" for i in range(N_SEGS)],
        y=seg_means_var,
        marker_color=CLUSTER_PALETTE,
        hovertemplate=[
            f"<b>{SEGMENT_NAMES[i]}</b><br>{var}: {seg_means_var[i]:,.2f}"
            f"<br>vs pop avg: {pop_mean:,.2f}<extra></extra>"
            for i in range(N_SEGS)
        ],
        showlegend=False,
        name=var
    ), row=row, col=col)
    # Population mean line
    fig3.add_hline(y=pop_mean, line_dash="dash", line_color=COLOR_NEUTRAL,
                   row=row, col=col,
                   annotation_text=f"Pop avg: {pop_mean:,.1f}",
                   annotation_position="top right")

fig3.update_layout(
    title="Segment Means vs Population Average — Top 6 Differentiating Variables<br>"
          "<sup>Dashed line = population mean | S0–S4 = segment IDs</sup>",
    height=550, dragmode="zoom"
)
sections.append(("fig", "Section 3 — Segment vs Population Mean (Top 6 Variables)", fig3))

# --- Section 4: Box Plots for Key Variables ---
box_vars = ['BALANCE_TO_LIMIT_RATIO', 'PRC_FULL_PAYMENT', 'CASH_ADVANCE_FREQUENCY',
            'PURCHASES_TRX', 'CREDIT_LIMIT']

fig4 = make_subplots(rows=1, cols=len(box_vars),
                      subplot_titles=box_vars, horizontal_spacing=0.07)
for col_n, var in enumerate(box_vars):
    for sid in range(N_SEGS):
        vals = df[df['segment'] == sid][var]
        fig4.add_trace(go.Box(
            y=vals, name=SEGMENT_NAMES[sid],
            marker_color=CLUSTER_PALETTE[sid], line_color=CLUSTER_PALETTE[sid],
            boxpoints=False,
            showlegend=(col_n == 0),
            hovertemplate=f"<b>{SEGMENT_NAMES[sid]}</b><br>Median: %{{median:.2f}}<extra></extra>"
        ), row=1, col=col_n + 1)
fig4.update_layout(
    title="Distribution by Segment — Key Behavioral Variables",
    height=500, dragmode="zoom",
    legend=dict(orientation='h', x=0, y=-0.15)
)
sections.append(("fig", "Section 4 — Distribution by Segment (Key Variables)", fig4))

# --- Section 5: Full Profiling Table ---
table_vars = PROFILE_VARS
header_vals = ['Variable', 'Population'] + [f"{SEGMENT_NAMES[i][:18]}<br>(n={seg_counts[i]:,})" for i in range(N_SEGS)] + ['Eta²', 'Sig?']

def fmt_val(val, var):
    if var in ['BALANCE_TO_LIMIT_RATIO', 'PRC_FULL_PAYMENT', 'CASH_ADVANCE_FREQUENCY',
               'BALANCE_FREQUENCY', 'PURCHASES_FREQUENCY', 'ONEOFF_PURCHASES_FREQUENCY',
               'PURCHASES_INSTALLMENTS_FREQUENCY']:
        return f"{val:.2f}"
    elif var in ['PURCHASES_TRX', 'TENURE']:
        return f"{val:.1f}"
    else:
        return f"${val:,.0f}"

var_col, pop_col = [], []
seg_cols = [[] for _ in range(N_SEGS)]
eta_col, sig_col = [], []

for var in table_vars:
    var_col.append(var)
    pop_col.append(fmt_val(pop_stats[var]['mean'], var))
    for sid in range(N_SEGS):
        seg_cols[sid].append(fmt_val(seg_stats[sid][var]['mean'], var))
    eta_col.append(f"{effect_sizes.get(var, 0):.3f}")
    sig_col.append("✓" if anova_pvals.get(var, 1.0) < 0.05 else "")

cell_colors_var = ['#f0f7ff' if i % 2 == 0 else 'white' for i in range(len(table_vars))]

fig5 = go.Figure(go.Table(
    header=dict(
        values=header_vals,
        fill_color=[COLOR_GROUP_1] * (2 + N_SEGS + 2),
        font=dict(color='white', size=10), align='center', height=36
    ),
    cells=dict(
        values=[var_col, pop_col] + seg_cols + [eta_col, sig_col],
        fill_color=[cell_colors_var] * (2 + N_SEGS + 2),
        align=['left', 'center'] + ['center'] * N_SEGS + ['center', 'center'],
        font=dict(size=10), height=26
    )
))
fig5.update_layout(title="Full Profiling Table — Variable Means by Segment",
                   height=max(600, 30 * len(table_vars) + 100))
sections.append(("fig", "Section 5 — Full Profiling Table", fig5))

# --- Section 6: Hypothesis Testing Results ---
hypotheses = [
    ("H1", "High-balance, low-purchase revolvers exist",
     "SUPPORTED",
     f"S0 (High-Utilization Revolvers, n=2,763) confirms this: avg BALANCE=${seg_stats[0]['BALANCE']['mean']:,.0f}, "
     f"PURCHASES=${seg_stats[0]['PURCHASES']['mean']:,.0f} (lowest of all segments), PRC={seg_stats[0]['PRC_FULL_PAYMENT']['mean']:.2f}. "
     f"S4 (Cash Advance Revolvers) is a related but distinct group: high balance driven by cash advances rather than purchase carry."),
    ("H2", "High-frequency transactors who pay in full exist",
     "SUPPORTED",
     f"S2 (Full-Payment Transactors, n=1,146) confirms this: PRC_FULL_PAYMENT={seg_stats[2]['PRC_FULL_PAYMENT']['mean']:.2f} (pays in full 77% of cycles), "
     f"near-zero balance (${seg_stats[2]['BALANCE']['mean']:,.0f}). "
     f"Note: S3 (Active Purchasers) is the high-frequency segment (58 transactions avg) but PRC=0.20 — they carry some balance. "
     f"The intake hypothesis blends two distinct profiles that appear as separate segments here."),
    ("H3", "Cash advance segment exists as a distinct behavioral group",
     "STRONGLY SUPPORTED",
     f"S4 (Cash Advance Revolvers, n=937) is the clearest segment in the dataset: avg cash advance=${seg_stats[4]['CASH_ADVANCE']['mean']:,.0f}, "
     f"CASH_ADVANCE_FREQUENCY={seg_stats[4]['CASH_ADVANCE_FREQUENCY']['mean']:.2f} (47% of cycles), "
     f"purchase activity minimal (${seg_stats[4]['PURCHASES']['mean']:,.0f} total purchases). "
     f"CASH_ADVANCE is the second-strongest differentiating variable by eta-squared."),
    ("H4", "Dormant / minimal-usage segment exists",
     "PARTIALLY SUPPORTED",
     f"S1 (Low-Balance Occasional Users, n=2,975) is the closest match: low BALANCE (${seg_stats[1]['BALANCE']['mean']:,.0f}), "
     f"low utilization ({seg_stats[1]['BALANCE_TO_LIMIT_RATIO']['mean']:.2f}), "
     f"modest purchase activity. However, no fully dormant segment emerged — all clusters show at least moderate engagement, "
     f"consistent with the intake's note that inactive accounts were excluded prior to data extraction."),
    ("H5", "Installment purchasers form a distinct segment from one-off purchasers",
     "SUPPORTED",
     f"S2 (Full-Payment Transactors) favors installments: INSTALLMENTS_PURCHASES=${seg_stats[2]['INSTALLMENTS_PURCHASES']['mean']:,.0f} vs "
     f"ONEOFF_PURCHASES=${seg_stats[2]['ONEOFF_PURCHASES']['mean']:,.0f}, PURCHASES_INSTALLMENTS_FREQUENCY={seg_stats[2]['PURCHASES_INSTALLMENTS_FREQUENCY']['mean']:.2f}. "
     f"S3 (Active Purchasers) is both-heavy but one-off dominant: ONEOFF=${seg_stats[3]['ONEOFF_PURCHASES']['mean']:,.0f} vs "
     f"INSTALLMENTS=${seg_stats[3]['INSTALLMENTS_PURCHASES']['mean']:,.0f}. "
     f"The segments are behaviorally distinct even if the installment/one-off split is not the primary defining dimension."),
]

hyp_rows = [(h[0], h[1], h[2], h[3]) for h in hypotheses]
verdict_colors = {'SUPPORTED': COLOR_FLAG_GREEN, 'STRONGLY SUPPORTED': COLOR_FLAG_GREEN, 'PARTIALLY SUPPORTED': COLOR_FLAG_AMBER}

fig6 = go.Figure(go.Table(
    header=dict(
        values=['#', 'Hypothesis', 'Verdict', 'Evidence'],
        fill_color=COLOR_GROUP_1,
        font=dict(color='white', size=11), align='left', height=32
    ),
    cells=dict(
        values=[
            [h[0] for h in hyp_rows],
            [h[1] for h in hyp_rows],
            [h[2] for h in hyp_rows],
            [h[3] for h in hyp_rows],
        ],
        fill_color=[
            ['white'] * 5,
            ['#f0f7ff' if i % 2 == 0 else 'white' for i in range(5)],
            ['#d4edda' if 'SUPPORTED' in h[2] else '#fff3cd' for h in hyp_rows],
            ['#f0f7ff' if i % 2 == 0 else 'white' for i in range(5)],
        ],
        align=['center', 'left', 'center', 'left'],
        font=dict(size=10), height=80
    )
))
fig6.update_layout(title="Hypothesis Testing Results", height=600)
sections.append(("fig", "Section 6 — Intake Hypothesis Testing", fig6))

# ============================================================
# WRITE HTML
# ============================================================
style = """
<style>
body{font-family:Arial,sans-serif;max-width:1450px;margin:0 auto;padding:20px;background:#f5f7fa}
h1{color:#2E86AB;border-bottom:3px solid #2E86AB;padding-bottom:10px}
h2{color:#1a5c7a;border-bottom:1px solid #cce0ec;padding-bottom:6px;margin-top:40px;font-size:1.1em}
.seg-card{border-radius:8px;padding:16px;margin:10px 0;border-left:5px solid #ccc;background:white;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
.seg-card h3{margin-top:0}
.seg-stat{display:inline-block;background:#f0f7ff;border-radius:4px;padding:4px 10px;margin:3px;font-size:12px}
.risk-flag{background:#fff0f0;border-left-color:#E84855}
</style>
"""

with open(output_path, "w") as f:
    f.write(f"<html><head><title>Profiling — Credit Card Segmentation</title>{style}</head><body>\n")
    f.write(f"<h1>Profiling Report — Credit Card Customer Segmentation</h1>\n")
    f.write(f"<p style='color:gray'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
            f"5 segments | {len(PROFILE_VARS)} variables profiled | {n_rows:,} accounts</p>\n")

    # Segment narrative cards
    f.write("<h2>Segment Narratives</h2>\n")
    risk_segs = {0, 4}
    for sid in range(N_SEGS):
        css_extra = " risk-flag" if sid in risk_segs else ""
        border_color = CLUSTER_PALETTE[sid]
        stats_html = ""
        key_stats = [
            ('Balance', f"${seg_stats[sid]['BALANCE']['mean']:,.0f}"),
            ('Utilization', f"{seg_stats[sid]['BALANCE_TO_LIMIT_RATIO']['mean']:.0%}"),
            ('Purchases', f"${seg_stats[sid]['PURCHASES']['mean']:,.0f}"),
            ('Cash Adv', f"${seg_stats[sid]['CASH_ADVANCE']['mean']:,.0f}"),
            ('PRC Full Pay', f"{seg_stats[sid]['PRC_FULL_PAYMENT']['mean']:.0%}"),
            ('Transactions', f"{seg_stats[sid]['PURCHASES_TRX']['mean']:.0f}"),
            ('Credit Limit', f"${seg_stats[sid]['CREDIT_LIMIT']['mean']:,.0f}"),
        ]
        for label, val in key_stats:
            stats_html += f"<span class='seg-stat'><b>{label}:</b> {val}</span>"

        f.write(f"""
        <div class='seg-card{css_extra}' style='border-left-color:{border_color}'>
          <h3 style='color:{border_color}'>{SEGMENT_NAMES[sid]}
            <span style='font-size:13px;font-weight:normal;color:#888'>
              — n={seg_counts[sid]:,} ({seg_pcts[sid]:.1f}%){' ⚠ Risk Flag' if sid in risk_segs else ''}
            </span>
          </h3>
          <p style='margin:8px 0;line-height:1.6'>{NARRATIVES[sid]}</p>
          <div style='margin-top:10px'>{stats_html}</div>
        </div>
        """)

    first_plotly = True
    for sec_type, sec_title, content in sections:
        f.write(f"<h2>{sec_title}</h2>\n")
        include_js = "cdn" if first_plotly else False
        f.write(content.to_html(full_html=False, include_plotlyjs=include_js) + "\n")
        first_plotly = False

    f.write("</body></html>")

print(f"[OK] Profiling report saved: {output_path}")
webbrowser.open("file://" + os.path.abspath(output_path))

# ============================================================
# PRINT SUMMARY FOR CHAT
# ============================================================
print("\n" + "=" * 65)
print("PROFILING SUMMARY")
print("=" * 65)
print(f"Variables profiled: {len(PROFILE_VARS)} | Segments: {N_SEGS} | Accounts: {n_rows:,}")

print("\nTOP 10 DIFFERENTIATING VARIABLES (by eta-squared):")
print(f"{'Rank':<5} {'Variable':<38} {'Eta²':>6} {'Effect':>10} {'p<0.05':>7}")
print("-" * 68)
for rank, (var, eta) in enumerate(ranked_vars[:10], 1):
    sig = "YES" if anova_pvals.get(var, 1.0) < 0.05 else "no"
    print(f"{rank:<5} {var:<38} {eta:>6.3f} {eta_label(eta):>10} {sig:>7}")

print("\nHYPOTHESIS VERDICTS:")
for h in hypotheses:
    print(f"  {h[0]}: {h[2]} — {h[1]}")

print("\nSEGMENT KEY STATS:")
for sid in range(N_SEGS):
    print(f"\n  {SEGMENT_NAMES[sid]} (n={seg_counts[sid]:,}, {seg_pcts[sid]:.1f}%)")
    for var in ['BALANCE', 'BALANCE_TO_LIMIT_RATIO', 'PURCHASES', 'CASH_ADVANCE',
                'PRC_FULL_PAYMENT', 'PURCHASES_TRX', 'CREDIT_LIMIT']:
        if var in seg_stats[sid]:
            v = seg_stats[sid][var]
            print(f"    {var}: mean={v['mean']:,.2f} | median={v['median']:,.2f}")
