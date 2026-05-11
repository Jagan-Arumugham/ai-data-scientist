import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import os
import webbrowser
from datetime import datetime

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# --- Setup ---
pio.templates.default = "plotly_white"
COLOR_GROUP_1 = "#2E86AB"
COLOR_GROUP_2 = "#E84855"
COLOR_NEUTRAL = "#6C757D"
COLOR_FLAG_RED = "#E84855"
COLOR_FLAG_AMBER = "#F4A261"
COLOR_FLAG_GREEN = "#2A9D8F"

analysis_id = "credit_card_segmentation"
base_dir = os.path.join("analyses", analysis_id)
data_path = os.path.join(base_dir, "data", "cc_general.csv")
output_dir = os.path.join(base_dir, "outputs", "eda_charts")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "eda_report.html")

# ============================================================
# LOAD DATA
# ============================================================
df = pd.read_csv(data_path)
n_rows, n_cols = df.shape

# ============================================================
# VARIABLE CLASSIFICATION
# ============================================================
identifier_cols = ['CUST_ID']
frequency_cols = [c for c in ['BALANCE_FREQUENCY', 'PURCHASES_FREQUENCY', 'ONEOFF_PURCHASES_FREQUENCY',
                               'PURCHASES_INSTALLMENTS_FREQUENCY', 'CASH_ADVANCE_FREQUENCY',
                               'PRC_FULL_PAYMENT'] if c in df.columns]
dollar_cols = [c for c in ['BALANCE', 'PURCHASES', 'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES',
                            'CASH_ADVANCE', 'PAYMENTS', 'MINIMUM_PAYMENTS', 'CREDIT_LIMIT'] if c in df.columns]
count_cols = [c for c in ['PURCHASES_TRX', 'CASH_ADVANCE_TRX'] if c in df.columns]
relationship_cols = [c for c in ['TENURE'] if c in df.columns]

all_continuous = [c for c in df.columns
                  if c not in identifier_cols and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]

# ============================================================
# GRAIN CHECK
# ============================================================
cust_id_unique = df['CUST_ID'].nunique() if 'CUST_ID' in df.columns else 0
is_unique_key = (cust_id_unique == n_rows)
grain_statement = "One row represents one active credit card account over a 6-month behavioral snapshot"

# ============================================================
# DUPLICATE CHECK
# ============================================================
full_dupes = df.duplicated().sum()
id_dupes = df['CUST_ID'].duplicated().sum() if 'CUST_ID' in df.columns else 0

# ============================================================
# NULL ANALYSIS
# ============================================================
null_counts = df.isnull().sum()
null_rates = (null_counts / n_rows * 100).round(2)

# ============================================================
# CARDINALITY
# ============================================================
cardinality = df.nunique()
zero_variance = cardinality[cardinality <= 1].index.tolist()

# ============================================================
# DESCRIPTIVE STATS
# ============================================================
desc = df[all_continuous].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T
desc['skewness'] = df[all_continuous].skew()
desc['null_rate_pct'] = null_rates[all_continuous]

# ============================================================
# ZERO / ONE MASS (bounded 0-1 variables)
# ============================================================
zero_mass = {}
one_mass = {}
for col in frequency_cols:
    zero_mass[col] = round((df[col] == 0).sum() / n_rows * 100, 1)
    one_mass[col] = round((df[col] == 1).sum() / n_rows * 100, 1)

# ============================================================
# OUTLIER ANALYSIS (IQR)
# ============================================================
outlier_info = {}
for col in dollar_cols + count_cols:
    vals = df[col].dropna()
    q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = int(((vals < lower) | (vals > upper)).sum())
    outlier_info[col] = {'count': n_out, 'pct': round(n_out / len(vals) * 100, 1),
                         'upper_fence': round(upper, 2), 'max': round(vals.max(), 2)}

# ============================================================
# CORRELATION
# ============================================================
corr_vars = [c for c in all_continuous if c in df.columns]
corr_matrix = df[corr_vars].corr()

high_corr_pairs = []
for i in range(len(corr_vars)):
    for j in range(i + 1, len(corr_vars)):
        r = corr_matrix.iloc[i, j]
        if abs(r) >= 0.70:
            high_corr_pairs.append({'col_a': corr_vars[i], 'col_b': corr_vars[j], 'corr': round(r, 3)})
high_corr_pairs.sort(key=lambda x: abs(x['corr']), reverse=True)

# ============================================================
# BIMODAL FLAGS
# ============================================================
bimodal_flags = []
for col in frequency_cols:
    if zero_mass.get(col, 0) > 20 and one_mass.get(col, 0) > 20:
        bimodal_flags.append(col)

# ============================================================
# BUILD REPORT SECTIONS
# ============================================================
sections = []  # list of (type, title, content)

# ------------------------------------------------------------------
# SECTION 1 — Dataset Overview (HTML)
# ------------------------------------------------------------------
structural_flags = []
if not is_unique_key:
    structural_flags.append(f"<li style='color:{COLOR_FLAG_RED}'>⚠ CUST_ID not fully unique — {id_dupes} duplicate IDs</li>")
if full_dupes > 0:
    structural_flags.append(f"<li style='color:{COLOR_FLAG_RED}'>⚠ {full_dupes} fully duplicate rows detected</li>")
if zero_variance:
    structural_flags.append(f"<li style='color:{COLOR_FLAG_AMBER}'>⚠ Zero-variance columns: {', '.join(zero_variance)}</li>")
if not structural_flags:
    structural_flags.append(f"<li style='color:{COLOR_FLAG_GREEN}'>✓ No immediate structural concerns</li>")

overview_html = f"""
<div style="background:white;border-radius:8px;padding:20px;margin:10px 0;box-shadow:0 1px 4px rgba(0,0,0,0.1)">
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <tr style="background:#f0f7ff"><td style="padding:10px;font-weight:bold;width:220px">Total Rows</td><td style="padding:10px">{n_rows:,}</td></tr>
    <tr><td style="padding:10px;font-weight:bold">Total Columns</td><td style="padding:10px">{n_cols}</td></tr>
    <tr style="background:#f0f7ff"><td style="padding:10px;font-weight:bold">Grain</td><td style="padding:10px">{grain_statement}</td></tr>
    <tr><td style="padding:10px;font-weight:bold">CUST_ID Unique</td><td style="padding:10px">{'✓ Yes — confirms customer-level grain' if is_unique_key else f'✗ No — {id_dupes} duplicates'}</td></tr>
    <tr style="background:#f0f7ff"><td style="padding:10px;font-weight:bold">Full Duplicate Rows</td><td style="padding:10px">{full_dupes}</td></tr>
    <tr><td style="padding:10px;font-weight:bold">Columns with Nulls</td><td style="padding:10px">{(null_counts > 0).sum()}</td></tr>
    <tr style="background:#f0f7ff"><td style="padding:10px;font-weight:bold">Target Variable</td><td style="padding:10px"><em>None — unsupervised segmentation. Cluster assignments will become the outcome.</em></td></tr>
    <tr><td style="padding:10px;font-weight:bold">Derived Feature Opportunity</td><td style="padding:10px">BALANCE_TO_LIMIT_RATIO = BALANCE / CREDIT_LIMIT (utilization rate — more meaningful than raw BALANCE alone)</td></tr>
  </table>
  <div style="margin-top:15px"><strong>Structural Checks:</strong><ul>{''.join(structural_flags)}</ul></div>
</div>
"""
sections.append(("html", "Section 1 — Dataset Overview", overview_html))

# ------------------------------------------------------------------
# SECTION 2 — Missingness Profile
# ------------------------------------------------------------------
null_df = pd.DataFrame({
    'column': null_rates.index,
    'null_rate': null_rates.values,
    'null_count': null_counts.values
}).sort_values('null_rate', ascending=True)

treatments = {
    'CREDIT_LIMIT': 'Structural missing (~1%). Flag rows; decide: median impute or exclude.',
    'MINIMUM_PAYMENTS': 'Structural missing (~3.5%). Flag rows; decide: median impute or exclude.',
    'CUST_ID': 'Identifier — exclude before clustering'
}
bar_colors = [COLOR_FLAG_RED if r > 20 else (COLOR_FLAG_AMBER if r > 5 else COLOR_FLAG_GREEN)
              for r in null_df['null_rate']]
hover_texts = [
    f"<b>{row['column']}</b><br>Null count: {int(row['null_count']):,}<br>Null rate: {row['null_rate']:.2f}%<br>"
    f"Recommendation: {treatments.get(row['column'], 'No action needed')}"
    for _, row in null_df.iterrows()
]

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    y=null_df['column'], x=null_df['null_rate'],
    orientation='h',
    marker_color=bar_colors,
    text=[f"{r:.1f}%" for r in null_df['null_rate']],
    textposition='outside',
    hovertemplate=[f"{h}<extra></extra>" for h in hover_texts],
    name=''
))
fig2.add_vline(x=20, line_dash="dash", line_color=COLOR_FLAG_RED,
               annotation_text="20% Flag Threshold", annotation_position="top right")
fig2.update_layout(
    title="Null Rate by Column — Flag if Above 20%",
    xaxis_title="Null Rate (%)", yaxis_title="",
    height=500, dragmode="zoom", showlegend=False,
    margin=dict(l=200)
)
sections.append(("fig", "Section 2 — Missingness Profile", fig2))

# ------------------------------------------------------------------
# SECTION 3 — PRC_FULL_PAYMENT Distribution (key behavioral signal)
# ------------------------------------------------------------------
vals3 = df['PRC_FULL_PAYMENT'].dropna()
mean3, median3, std3 = vals3.mean(), vals3.median(), vals3.std()

fig3 = go.Figure()
fig3.add_trace(go.Histogram(
    x=vals3, nbinsx=50,
    marker_color=COLOR_GROUP_1, opacity=0.75,
    name='Distribution',
    hovertemplate="Value: %{x:.2f}<br>Count: %{y}<extra></extra>"
))

if HAS_SCIPY:
    try:
        kde = stats.gaussian_kde(vals3, bw_method=0.15)
        x_kde = np.linspace(0, 1, 300)
        bin_width = 1 / 50
        y_kde = kde(x_kde) * len(vals3) * bin_width
        fig3.add_trace(go.Scatter(
            x=x_kde, y=y_kde, mode='lines',
            line=dict(color=COLOR_GROUP_2, width=2),
            name='KDE',
            hovertemplate="Value: %{x:.2f}<br>Density: %{y:.1f}<extra></extra>"
        ))
    except Exception:
        pass

fig3.add_vline(x=mean3, line_dash="dash", line_color=COLOR_NEUTRAL,
               annotation_text=f"Mean: {mean3:.2f}")
fig3.update_layout(
    title=(f"Distribution of PRC_FULL_PAYMENT — Proportion of Statement Cycles Paid in Full<br>"
           f"<sup>Mean: {mean3:.2f} | Median: {median3:.2f} | Std: {std3:.2f} | "
           f"Zero-mass (revolvers): {zero_mass.get('PRC_FULL_PAYMENT', 0):.1f}% | "
           f"One-mass (transactors): {one_mass.get('PRC_FULL_PAYMENT', 0):.1f}% — ⚠ Expected bimodal</sup>"),
    xaxis_title="Proportion of Full Payments (0 = never paid in full, 1 = always paid in full)",
    yaxis_title="Count",
    height=430, dragmode="zoom"
)
sections.append(("fig", "Section 3 — Key Repayment Behavior: PRC_FULL_PAYMENT", fig3))

# ------------------------------------------------------------------
# SECTION 4 — Continuous Variable Distributions (dropdown)
# ------------------------------------------------------------------
ordered_vars = (
    ['PRC_FULL_PAYMENT', 'BALANCE', 'CREDIT_LIMIT', 'PURCHASES', 'CASH_ADVANCE',
     'PAYMENTS', 'MINIMUM_PAYMENTS', 'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES',
     'BALANCE_FREQUENCY', 'PURCHASES_FREQUENCY', 'CASH_ADVANCE_FREQUENCY',
     'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
     'PURCHASES_TRX', 'CASH_ADVANCE_TRX', 'TENURE']
)
ordered_vars = [c for c in ordered_vars if c in df.columns]

traces4 = []
annotations4 = []
for i, col in enumerate(ordered_vars):
    vals = df[col].dropna()
    mean_v, median_v, std_v, skew_v = vals.mean(), vals.median(), vals.std(), vals.skew()
    null_r = null_rates[col]
    nbins = 40 if col in frequency_cols else min(70, max(20, int(np.sqrt(len(vals)))))
    bimodal_note = " | ⚠ Bimodal — mass at both extremes" if col in bimodal_flags else ""

    traces4.append(go.Histogram(
        x=vals, nbinsx=nbins,
        marker_color=COLOR_GROUP_1, opacity=0.75,
        name=col, visible=(i == 0),
        hovertemplate=f"Value: %{{x}}<br>Count: %{{y}}<extra></extra>"
    ))
    annotations4.append(dict(
        text=(f"Mean: {mean_v:,.2f} | Median: {median_v:,.2f} | Std: {std_v:,.2f} | "
              f"Skew: {skew_v:.2f} | Nulls: {null_r:.1f}%{bimodal_note}"),
        xref='paper', yref='paper', x=0.5, y=1.07,
        showarrow=False, font=dict(size=11, color='gray'),
        bgcolor='rgba(255,255,255,0.8)'
    ))

buttons4 = []
for i, col in enumerate(ordered_vars):
    buttons4.append(dict(
        label=col,
        method="update",
        args=[{"visible": [j == i for j in range(len(ordered_vars))]},
              {"title": f"Distribution of {col}", "xaxis.title": col,
               "annotations": [annotations4[i]]}]
    ))

fig4 = go.Figure(data=traces4)
fig4.update_layout(
    title=f"Distribution of {ordered_vars[0]}",
    xaxis_title=ordered_vars[0], yaxis_title="Count",
    height=460, dragmode="zoom",
    annotations=[annotations4[0]],
    updatemenus=[dict(
        active=0, buttons=buttons4,
        direction="down", showactive=True,
        x=0.0, xanchor="left", y=1.18, yanchor="top",
        bgcolor="white", bordercolor="#ccc"
    )]
)
sections.append(("fig", "Section 4 — Continuous Variable Distributions (use dropdown to switch)", fig4))

# ------------------------------------------------------------------
# SECTION 5 — Frequency Variable Profiles (bounded 0-1 variables)
# ------------------------------------------------------------------
n_freq = len(frequency_cols)
fig5 = make_subplots(
    rows=n_freq, cols=1,
    subplot_titles=[
        f"{col}  |  Zero-mass: {zero_mass.get(col, 0):.1f}%  |  One-mass: {one_mass.get(col, 0):.1f}%"
        for col in frequency_cols
    ],
    vertical_spacing=0.06
)
for i, col in enumerate(frequency_cols):
    vals = df[col].dropna()
    fig5.add_trace(go.Histogram(
        x=vals, nbinsx=40,
        marker_color=COLOR_GROUP_1, opacity=0.75,
        name=col, showlegend=False,
        hovertemplate=f"Value: %{{x:.2f}}<br>Count: %{{y}}<extra></extra>"
    ), row=i + 1, col=1)

fig5.update_layout(
    title="Bounded Frequency Variable Profiles (0–1 Scale)<br>"
          "<sup>Check mass at extremes — variables with >40% zeros may behave as binary flags</sup>",
    height=200 * n_freq, dragmode="zoom"
)
sections.append(("fig", "Section 5 — Frequency Variable Profiles", fig5))

# ------------------------------------------------------------------
# SECTION 6 — Outlier Summary
# ------------------------------------------------------------------
outlier_vars = dollar_cols + count_cols
fig6 = go.Figure()
for col in outlier_vars:
    vals = df[col].dropna()
    fig6.add_trace(go.Box(
        x=vals, name=col, orientation='h',
        boxpoints='outliers',
        marker=dict(color=COLOR_GROUP_2, opacity=0.5, size=3),
        line=dict(color=COLOR_GROUP_1),
        hovertemplate=f"<b>{col}</b><br>Value: %{{x:,.2f}}<extra></extra>"
    ))

fig6.update_layout(
    title="Outlier Summary — Dollar and Count Variables<br><sup>Dots = individual outlier points (beyond Q3 + 1.5×IQR)</sup>",
    xaxis_title="Value", height=max(450, 55 * len(outlier_vars)),
    dragmode="zoom", showlegend=False,
    margin=dict(l=200)
)
sections.append(("fig", "Section 6 — Outlier Summary", fig6))

# ------------------------------------------------------------------
# SECTION 7 — Correlation Heatmap
# ------------------------------------------------------------------
corr_sub = df[corr_vars].corr()
mask = np.triu(np.ones(corr_sub.shape, dtype=bool), k=1)

z_vals = corr_sub.values.copy().astype(float)
z_vals[mask] = np.nan

text_vals = []
for i in range(len(corr_vars)):
    row_text = []
    for j in range(len(corr_vars)):
        if not mask[i, j]:
            row_text.append(f"{corr_sub.iloc[i, j]:.2f}")
        else:
            row_text.append("")
    text_vals.append(row_text)

fig7 = go.Figure(go.Heatmap(
    z=z_vals,
    x=corr_vars, y=corr_vars,
    colorscale='RdBu', zmid=0, zmin=-1, zmax=1,
    text=text_vals, texttemplate="%{text}",
    hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>",
    colorbar=dict(title="r")
))
fig7.update_layout(
    title="Correlation Matrix — Pairs Above |0.70| Flagged",
    height=750, dragmode="zoom",
    xaxis=dict(tickangle=45, tickfont=dict(size=10)),
    yaxis=dict(tickfont=dict(size=10)),
    margin=dict(b=120, l=120)
)
sections.append(("fig", "Section 7 — Correlation Heatmap", fig7))

# ------------------------------------------------------------------
# SECTION 8 — Key Variable Pair Scatter Plots
# ------------------------------------------------------------------
key_pairs = [
    ('BALANCE', 'PRC_FULL_PAYMENT', 'Revolver vs Transactor axis'),
    ('CASH_ADVANCE', 'PURCHASES', 'Cash-advance vs purchase behavior'),
    ('BALANCE', 'CREDIT_LIMIT', 'Balance vs credit limit (utilization)'),
    ('PURCHASES_FREQUENCY', 'PRC_FULL_PAYMENT', 'Purchase frequency vs repayment discipline'),
    ('CASH_ADVANCE_FREQUENCY', 'BALANCE_FREQUENCY', 'Cash advance vs balance carry frequency'),
    ('ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES', 'One-off vs installment purchase split'),
]
key_pairs = [(a, b, label) for a, b, label in key_pairs if a in df.columns and b in df.columns]

n_pairs = len(key_pairs)
fig8_rows = (n_pairs + 1) // 2
fig8 = make_subplots(
    rows=fig8_rows, cols=2,
    subplot_titles=[label for _, _, label in key_pairs],
    horizontal_spacing=0.10, vertical_spacing=0.12
)
for i, (col_a, col_b, _) in enumerate(key_pairs):
    row, col_n = i // 2 + 1, i % 2 + 1
    sample = df[[col_a, col_b]].dropna().sample(min(2000, len(df)), random_state=42)
    fig8.add_trace(go.Scatter(
        x=sample[col_a], y=sample[col_b],
        mode='markers',
        marker=dict(color=COLOR_GROUP_1, opacity=0.35, size=4),
        showlegend=False,
        hovertemplate=f"{col_a}: %{{x:,.2f}}<br>{col_b}: %{{y:,.2f}}<extra></extra>"
    ), row=row, col=col_n)
    fig8.update_xaxes(title_text=col_a, row=row, col=col_n)
    fig8.update_yaxes(title_text=col_b, row=row, col=col_n)

fig8.update_layout(
    title="Key Variable Relationships — Analytically Relevant Pairs<br>"
          "<sup>Sampled to 2,000 points per plot for clarity</sup>",
    height=380 * fig8_rows, dragmode="select"
)
sections.append(("fig", "Section 8 — Key Variable Relationships", fig8))

# ------------------------------------------------------------------
# SECTION 9 — TENURE Distribution
# ------------------------------------------------------------------
tenure_counts = df['TENURE'].value_counts().sort_index()
tenure_pcts = (tenure_counts / n_rows * 100).round(1)
fig9 = go.Figure()
fig9.add_trace(go.Bar(
    x=tenure_counts.index.astype(str),
    y=tenure_counts.values,
    marker_color=[COLOR_FLAG_RED if p > 80 else COLOR_GROUP_1 for p in tenure_pcts],
    text=[f"{p:.1f}%" for p in tenure_pcts],
    textposition='outside',
    hovertemplate="Tenure: %{x} months<br>Count: %{y:,}<br>Share: %{text}<extra></extra>",
    name='TENURE'
))
fig9.update_layout(
    title=f"TENURE Distribution — Months as Card Holder<br>"
          f"<sup>Range: {int(df['TENURE'].min())}–{int(df['TENURE'].max())} months | Low variance — likely a weak segmentation variable</sup>",
    xaxis_title="Tenure (months)", yaxis_title="Count",
    height=380, dragmode="zoom", showlegend=False
)
sections.append(("fig", "Section 9 — Tenure Distribution", fig9))

# ------------------------------------------------------------------
# SECTION 10 — Data Quality Summary Table
# ------------------------------------------------------------------
table_rows = []
for col in df.columns:
    dtype_str = str(df[col].dtype)
    null_c = int(null_counts[col])
    null_r = float(null_rates[col])
    distinct = int(cardinality[col])
    flags = []
    if null_r > 20:
        flags.append("High nulls (>20%)")
    if distinct > 0.8 * n_rows and col not in identifier_cols:
        flags.append("High cardinality")
    if distinct <= 1:
        flags.append("Zero variance")
    if col in identifier_cols:
        flags.append("Identifier — exclude")
    table_rows.append([col, dtype_str, null_c, f"{null_r:.2f}%", distinct, "; ".join(flags)])

tdf = pd.DataFrame(table_rows, columns=['Column', 'Type', 'Null Count', 'Null Rate', 'Distinct Values', 'Flags'])
row_fill = ['#ffe5e5' if row[-1] else ('#f8f9fa' if i % 2 == 0 else 'white')
            for i, row in tdf.iterrows()]

fig10 = go.Figure(go.Table(
    header=dict(
        values=list(tdf.columns),
        fill_color=COLOR_GROUP_1,
        font=dict(color='white', size=12), align='left',
        height=32
    ),
    cells=dict(
        values=[tdf[c] for c in tdf.columns],
        fill_color=[row_fill] * len(tdf.columns),
        align='left', font=dict(size=11), height=28
    )
))
fig10.update_layout(title="Data Quality Summary — All Columns", height=650)
sections.append(("fig", "Section 10 — Data Quality Summary Table", fig10))

# ============================================================
# WRITE HTML FILE
# ============================================================
style = """
<style>
body{font-family:Arial,sans-serif;max-width:1400px;margin:0 auto;padding:20px;background:#f5f7fa}
h1{color:#2E86AB;border-bottom:3px solid #2E86AB;padding-bottom:10px}
h2{color:#1a5c7a;border-bottom:1px solid #cce0ec;padding-bottom:6px;margin-top:40px;font-size:1.1em}
p.meta{color:#888;font-size:13px;margin-top:-5px}
</style>
"""

with open(output_path, "w") as f:
    f.write(f"<html><head><title>EDA — Credit Card Segmentation</title>{style}</head><body>\n")
    f.write(f"<h1>EDA Report — Credit Card Customer Segmentation</h1>\n")
    f.write(f"<p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
            f"{n_rows:,} rows × {n_cols} columns | analysis_id: {analysis_id}</p>\n")

    first_plotly = True
    for sec_type, sec_title, content in sections:
        f.write(f"<h2>{sec_title}</h2>\n")
        if sec_type == "html":
            f.write(content + "\n")
        else:
            include_js = "cdn" if first_plotly else False
            f.write(content.to_html(full_html=False, include_plotlyjs=include_js) + "\n")
            first_plotly = False

    f.write("</body></html>")

print(f"[OK] HTML report saved: {output_path}")

# PNG export for PRC_FULL_PAYMENT (most likely to be shared)
try:
    png_path = os.path.join(output_dir, "prc_full_payment_distribution.png")
    fig3.write_image(png_path)
    print(f"[OK] PNG saved: {png_path}")
except Exception as e:
    print(f"[SKIP] PNG export skipped: {e}")

# Open in browser
webbrowser.open("file://" + os.path.abspath(output_path))
print("[OK] Report opened in browser.")

# ============================================================
# PRINT SUMMARY STATS FOR CHAT
# ============================================================
print("\n" + "=" * 60)
print("EDA SUMMARY STATS")
print("=" * 60)
print(f"Rows: {n_rows:,}  |  Columns: {n_cols}")
print(f"CUST_ID unique key: {is_unique_key}  |  Full dupes: {full_dupes}")

print("\nNULL RATES (non-zero):")
for col, rate in null_rates[null_rates > 0].sort_values(ascending=False).items():
    print(f"  {col}: {rate:.2f}%  (count: {int(null_counts[col])})")

print("\nFREQUENCY VARIABLE ZERO/ONE MASS:")
for col in frequency_cols:
    print(f"  {col}: {zero_mass.get(col,0):.1f}% zeros | {one_mass.get(col,0):.1f}% ones")

print("\nBIMODAL FLAGS:", bimodal_flags if bimodal_flags else "None")

print(f"\nHIGH CORRELATION PAIRS (|r| >= 0.70) — top 15:")
for p in high_corr_pairs[:15]:
    flag = " *** NEAR-CERTAIN REDUNDANCY" if abs(p['corr']) >= 0.90 else (" ** FLAG" if abs(p['corr']) >= 0.70 else "")
    print(f"  {p['col_a']} vs {p['col_b']}: r={p['corr']:.3f}{flag}")

print("\nOUTLIER COUNTS (IQR method):")
for col, info in outlier_info.items():
    print(f"  {col}: {info['count']} outliers ({info['pct']:.1f}%) | fence: {info['upper_fence']:,.0f} | max: {info['max']:,.0f}")

print("\nDESC STATS (mean | median | std | skew | null%):")
for col in ordered_vars:
    if col in desc.index:
        r = desc.loc[col]
        print(f"  {col}: {r['mean']:.2f} | {r['50%']:.2f} | {r['std']:.2f} | {r['skewness']:.2f} | {r['null_rate_pct']:.1f}%")
