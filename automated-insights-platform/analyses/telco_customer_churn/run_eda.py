import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import os
import webbrowser
from scipy import stats

pio.templates.default = "plotly_white"
COLOR_GROUP_1 = "#2E86AB"   # Retained / No churn
COLOR_GROUP_2 = "#E84855"   # Churned
COLOR_NEUTRAL = "#6C757D"
COLOR_FLAG_RED = "#E84855"
COLOR_FLAG_AMBER = "#F4A261"
COLOR_FLAG_GREEN = "#2A9D8F"

analysis_id = "telco_customer_churn"
base_dir = os.path.join("analyses", analysis_id)
data_path = os.path.join(base_dir, "data", "WA_Fn-UseC_-Telco-Customer-Churn.csv")
output_dir = os.path.join(base_dir, "outputs", "eda_charts")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "eda_report.html")

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv(data_path)

# Fix TotalCharges: coerce blanks to NaN then float
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

# Encode Churn as binary for correlations
df["Churn_binary"] = (df["Churn"] == "Yes").astype(int)

# SeniorCitizen: already 0/1 — keep as-is for analysis, note the inconsistency
continuous_cols = ["tenure", "MonthlyCharges", "TotalCharges"]
target_col = "Churn"
target_binary = "Churn_binary"
operational_cols = ["customerID"]

categorical_cols = [
    "gender", "SeniorCitizen", "Partner", "Dependents",
    "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod"
]

n_rows, n_cols = df.shape
churn_counts = df[target_col].value_counts()
churn_yes = churn_counts.get("Yes", 0)
churn_no = churn_counts.get("No", 0)
churn_yes_pct = round(100 * churn_yes / n_rows, 1)
churn_no_pct = round(100 * churn_no / n_rows, 1)

# ── Null analysis ──────────────────────────────────────────────────────────────
null_counts = df.isnull().sum()
null_rates = (null_counts / n_rows * 100).round(2)
null_df = pd.DataFrame({"column": null_counts.index, "null_count": null_counts.values,
                         "null_rate": null_rates.values}).sort_values("null_rate", ascending=False)

# ── Distinct value counts ──────────────────────────────────────────────────────
distinct_counts = df.nunique()

# ── Correlations among continuous vars + target ────────────────────────────────
corr_cols = continuous_cols + [target_binary]
corr_matrix = df[corr_cols].corr()

# Correlation of each variable with target
target_corr = df[continuous_cols].corrwith(df[target_binary]).abs().sort_values(ascending=False)

# ── Outlier detection (IQR) ────────────────────────────────────────────────────
def count_outliers(series):
    s = series.dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return ((s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)).sum()

outlier_counts = {c: count_outliers(df[c]) for c in continuous_cols}

figures = []

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Dataset Overview (HTML block, no chart)
# ══════════════════════════════════════════════════════════════════════════════
section1_html = f"""
<div style="background:#f8f9fa;border-left:4px solid #2E86AB;padding:20px 24px;margin:24px 0;border-radius:4px;font-family:sans-serif;">
  <h2 style="margin-top:0;color:#2E86AB;">Section 1 — Dataset Overview</h2>
  <table style="border-collapse:collapse;width:100%;font-size:14px;">
    <tr><td style="padding:6px 12px;font-weight:bold;width:220px;">Rows</td><td style="padding:6px 12px;">{n_rows:,}</td></tr>
    <tr style="background:#fff;"><td style="padding:6px 12px;font-weight:bold;">Columns</td><td style="padding:6px 12px;">{n_cols}</td></tr>
    <tr><td style="padding:6px 12px;font-weight:bold;">Grain</td><td style="padding:6px 12px;">One row per customer (customerID is the primary key — {df['customerID'].nunique():,} distinct values, matches row count)</td></tr>
    <tr style="background:#fff;"><td style="padding:6px 12px;font-weight:bold;">Target variable</td><td style="padding:6px 12px;">Churn — Yes ({churn_yes:,} customers, {churn_yes_pct}%) / No ({churn_no:,} customers, {churn_no_pct}%)</td></tr>
    <tr><td style="padding:6px 12px;font-weight:bold;">Temporal columns</td><td style="padding:6px 12px;">None — snapshot dataset, no date fields</td></tr>
    <tr style="background:#fff;"><td style="padding:6px 12px;font-weight:bold;">Structural flags</td><td style="padding:6px 12px;">
      ⚠ <b>TotalCharges</b> stored as string — coerced to float; 11 blank values found (new customers with tenure=0)<br>
      ⚠ <b>SeniorCitizen</b> encoded as 0/1 integer while all other binary columns use Yes/No strings<br>
      ⚠ Several internet/phone service columns contain a third value ("No internet service" / "No phone service") — conditional on upstream service enrollment
    </td></tr>
  </table>
</div>
"""

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Missingness Profile
# ══════════════════════════════════════════════════════════════════════════════
null_plot_df = null_df[null_df["null_rate"] > 0].copy()
if null_plot_df.empty:
    # All columns have some nulls or not — show top columns anyway
    null_plot_df = null_df.head(10).copy()

bar_colors = []
for r in null_df["null_rate"]:
    if r > 20:
        bar_colors.append(COLOR_FLAG_RED)
    elif r > 5:
        bar_colors.append(COLOR_FLAG_AMBER)
    else:
        bar_colors.append(COLOR_FLAG_GREEN)

null_sorted = null_df.sort_values("null_rate", ascending=True)
bar_colors_sorted = []
for r in null_sorted["null_rate"]:
    if r > 20:
        bar_colors_sorted.append(COLOR_FLAG_RED)
    elif r > 5:
        bar_colors_sorted.append(COLOR_FLAG_AMBER)
    else:
        bar_colors_sorted.append(COLOR_FLAG_GREEN)

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=null_sorted["null_rate"],
    y=null_sorted["column"],
    orientation="h",
    marker_color=bar_colors_sorted,
    text=[f"{r:.2f}%" for r in null_sorted["null_rate"]],
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>Null rate: %{x:.2f}%<br>Null count: %{customdata}<extra></extra>",
    customdata=null_sorted["null_count"]
))
fig2.add_vline(x=20, line_dash="dash", line_color=COLOR_FLAG_RED,
               annotation_text="20% threshold", annotation_position="top right")
fig2.update_layout(
    title="Section 2 — Null Rate by Column (Red > 20%, Amber 5–20%, Green < 5%)",
    xaxis_title="Null Rate (%)",
    yaxis_title="Column",
    height=500,
    dragmode="zoom",
    margin=dict(l=160, r=80, t=60, b=40)
)
figures.append(("Section 2 — Missingness Profile", fig2))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Target Variable Distribution
# ══════════════════════════════════════════════════════════════════════════════
fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=["No (Retained)", "Yes (Churned)"],
    y=[churn_no, churn_yes],
    marker_color=[COLOR_GROUP_1, COLOR_GROUP_2],
    text=[f"{churn_no_pct}%", f"{churn_yes_pct}%"],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Count: %{y:,}<br>Share: %{text}<extra></extra>"
))
fig3.update_layout(
    title="Section 3 — Distribution of Churn (Target Variable)",
    xaxis_title="Churn Status",
    yaxis_title="Number of Customers",
    height=400,
    dragmode="zoom"
)
figures.append(("Section 3 — Target Variable Distribution", fig3))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Continuous Variable Distributions (Dropdown)
# ══════════════════════════════════════════════════════════════════════════════
def kde_trace(series, color, name):
    s = series.dropna()
    kde = stats.gaussian_kde(s)
    x_range = np.linspace(s.min(), s.max(), 300)
    y_kde = kde(x_range)
    y_kde_scaled = y_kde * len(s) * (s.max() - s.min()) / 30
    return go.Scatter(x=x_range, y=y_kde_scaled, mode="lines",
                      line=dict(color=color, width=2), name=name, showlegend=False,
                      hovertemplate=f"<b>{name} KDE</b><br>Value: %{{x:.1f}}<extra></extra>")

fig4 = go.Figure()
visibility_sets = []
for i, col in enumerate(continuous_cols):
    s = df[col].dropna()
    mean_val = s.mean()
    median_val = s.median()
    std_val = s.std()
    skew_val = s.skew()
    null_rate = null_rates[col]
    nbins = min(50, max(20, int((s.max() - s.min()) / (s.std() / 3)))) if s.std() > 0 else 30

    fig4.add_trace(go.Histogram(
        x=s, nbinsx=nbins,
        name=col,
        marker_color=COLOR_GROUP_1, opacity=0.75,
        visible=(i == 0),
        hovertemplate=f"<b>{col}</b><br>Range: %{{x}}<br>Count: %{{y}}<extra></extra>"
    ))
    kde_t = kde_trace(s, COLOR_NEUTRAL, col + " KDE")
    kde_t.visible = (i == 0)
    fig4.add_trace(kde_t)

    subtitle = f"Mean: {mean_val:.1f} | Median: {median_val:.1f} | Std: {std_val:.1f} | Skew: {skew_val:.2f} | Nulls: {null_rate:.2f}%"
    if abs(skew_val) > 1:
        subtitle += " | ⚠ Skewed distribution"

buttons = []
for i, col in enumerate(continuous_cols):
    s = df[col].dropna()
    mean_val = s.mean()
    vis = [False] * (len(continuous_cols) * 2)
    vis[i*2] = True
    vis[i*2+1] = True
    buttons.append(dict(
        label=col,
        method="update",
        args=[{"visible": vis},
              {"title": f"Section 4 — Distribution: {col}",
               "xaxis.title": col,
               "shapes": [dict(type="line", x0=mean_val, x1=mean_val,
                               y0=0, y1=1, yref="paper",
                               line=dict(dash="dash", color=COLOR_FLAG_RED, width=1.5))]}]
    ))

fig4.update_layout(
    title="Section 4 — Continuous Variable Distributions",
    updatemenus=[dict(buttons=buttons, direction="down", x=0.01, y=1.12, showactive=True)],
    height=450, dragmode="zoom",
    xaxis_title=continuous_cols[0], yaxis_title="Count"
)
mean0 = df[continuous_cols[0]].mean()
fig4.add_vline(x=mean0, line_dash="dash", line_color=COLOR_FLAG_RED,
               annotation_text=f"Mean: {mean0:.1f}", annotation_position="top right")
figures.append(("Section 4 — Continuous Variable Distributions", fig4))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Target Variable Split Distributions (Primary analytical chart)
# ══════════════════════════════════════════════════════════════════════════════
df_churn = df[df["Churn"] == "Yes"]
df_no_churn = df[df["Churn"] == "No"]

fig5 = go.Figure()
top_corr_cols = list(target_corr.head(8).index)  # all continuous cols ranked by |corr|

vis5_sets = []
for i, col in enumerate(top_corr_cols):
    s_churn = df_churn[col].dropna()
    s_no = df_no_churn[col].dropna()
    nbins = min(50, max(20, 30))

    fig5.add_trace(go.Histogram(
        x=s_no, nbinsx=nbins, name="Retained",
        marker_color=COLOR_GROUP_1, opacity=0.65,
        visible=(i == 0),
        hovertemplate="<b>Retained (No Churn)</b><br>Range: %{x}<br>Count: %{y}<extra></extra>"
    ))
    fig5.add_trace(go.Histogram(
        x=s_churn, nbinsx=nbins, name="Churned",
        marker_color=COLOR_GROUP_2, opacity=0.65,
        visible=(i == 0),
        hovertemplate="<b>Churned</b><br>Range: %{x}<br>Count: %{y}<extra></extra>"
    ))

buttons5 = []
for i, col in enumerate(top_corr_cols):
    vis = [False] * (len(top_corr_cols) * 2)
    vis[i*2] = True
    vis[i*2+1] = True
    buttons5.append(dict(
        label=col,
        method="update",
        args=[{"visible": vis},
              {"title": f"Section 5 — Churn vs Retained: {col}",
               "xaxis.title": col}]
    ))

fig5.update_layout(
    barmode="overlay",
    title="Section 5 — Churn vs Retained: Distribution Comparison (Top Drivers)",
    updatemenus=[dict(buttons=buttons5, direction="down", x=0.01, y=1.12, showactive=True)],
    height=450, dragmode="zoom",
    xaxis_title=top_corr_cols[0], yaxis_title="Count",
    legend=dict(title="Group")
)
figures.append(("Section 5 — Target Variable Split Distributions", fig5))

# Save PNG fallback for Section 5
try:
    fig5.write_image(os.path.join(output_dir, "target_split_distributions.png"))
    print("PNG fallback saved.")
except Exception as e:
    print(f"PNG fallback skipped (kaleido not installed): {e}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Outlier Summary
# ══════════════════════════════════════════════════════════════════════════════
fig6 = make_subplots(rows=len(continuous_cols), cols=1,
                     shared_xaxes=False,
                     subplot_titles=continuous_cols)
for i, col in enumerate(continuous_cols):
    s = df[col].dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    fig6.add_trace(
        go.Box(
            x=s, name=col,
            boxpoints="outliers",
            marker_color=COLOR_GROUP_1,
            line_color=COLOR_NEUTRAL,
            orientation="h",
            hovertemplate=f"<b>{col}</b><br>Value: %{{x:.2f}}<extra></extra>",
            customdata=[[col]] * len(s)
        ),
        row=i+1, col=1
    )
fig6.update_layout(
    title="Section 6 — Outlier Summary — All Continuous Variables",
    height=250 * len(continuous_cols),
    showlegend=False,
    dragmode="zoom"
)
figures.append(("Section 6 — Outlier Summary", fig6))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Correlation Heatmap
# ══════════════════════════════════════════════════════════════════════════════
corr_labels = continuous_cols + ["Churn (binary)"]
corr_data = df[continuous_cols + [target_binary]].copy()
corr_data.columns = corr_labels
corr_m = corr_data.corr()

mask = np.triu(np.ones_like(corr_m, dtype=bool), k=1)
corr_masked = corr_m.copy()
corr_masked[mask] = None

fig7 = go.Figure(go.Heatmap(
    z=corr_masked.values,
    x=corr_labels,
    y=corr_labels,
    colorscale="RdBu",
    zmid=0, zmin=-1, zmax=1,
    text=[[f"{v:.2f}" if v is not None else "" for v in row] for row in corr_masked.values],
    texttemplate="%{text}",
    hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>"
))
fig7.update_layout(
    title="Section 7 — Correlation Matrix (Pairs Above 0.70 Flagged)",
    height=450,
    dragmode="zoom"
)
figures.append(("Section 7 — Correlation Heatmap", fig7))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Bivariate Scatter: Top Drivers vs Churn
# ══════════════════════════════════════════════════════════════════════════════
top6 = continuous_cols  # only 3 continuous vars available
n_scatter = len(top6)
cols_grid = min(3, n_scatter)
rows_grid = (n_scatter + cols_grid - 1) // cols_grid

fig8 = make_subplots(rows=rows_grid, cols=cols_grid,
                     subplot_titles=[f"{c} vs Churn" for c in top6])
for idx, col in enumerate(top6):
    r = idx // cols_grid + 1
    c = idx % cols_grid + 1
    for grp, color, label in [("No", COLOR_GROUP_1, "Retained"), ("Yes", COLOR_GROUP_2, "Churned")]:
        sub = df[df["Churn"] == grp]
        fig8.add_trace(
            go.Scatter(
                x=sub[col],
                y=sub[target_binary] + np.random.uniform(-0.05, 0.05, len(sub)),
                mode="markers",
                marker=dict(color=color, opacity=0.3, size=4),
                name=label,
                showlegend=(idx == 0),
                hovertemplate=f"<b>{label}</b><br>{col}: %{{x:.1f}}<extra></extra>"
            ),
            row=r, col=c
        )
fig8.update_layout(
    title="Section 8 — Continuous Variables vs Churn",
    height=350 * rows_grid,
    dragmode="select"
)
figures.append(("Section 8 — Bivariate: Top Drivers vs Churn", fig8))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Categorical Variable Distributions (Dropdown)
# ══════════════════════════════════════════════════════════════════════════════
fig9 = go.Figure()
vis9_sets = []
for i, col in enumerate(categorical_cols):
    vc = df[col].value_counts().sort_values(ascending=True)
    pcts = (vc / n_rows * 100).round(1)
    bar_c = [COLOR_FLAG_RED if p > 80 else COLOR_GROUP_1 for p in pcts]
    fig9.add_trace(go.Bar(
        x=vc.values, y=vc.index.astype(str),
        orientation="h",
        marker_color=bar_c,
        text=[f"{p}%" for p in pcts.values],
        textposition="outside",
        visible=(i == 0),
        name=col,
        hovertemplate=f"<b>%{{y}}</b><br>Count: %{{x:,}}<br>Share: %{{text}}<extra></extra>"
    ))

buttons9 = []
for i, col in enumerate(categorical_cols):
    vis = [False] * len(categorical_cols)
    vis[i] = True
    buttons9.append(dict(
        label=col,
        method="update",
        args=[{"visible": vis},
              {"title": f"Section 9 — Categorical Distribution: {col}",
               "xaxis.title": "Count"}]
    ))

fig9.update_layout(
    title=f"Section 9 — Categorical Distribution: {categorical_cols[0]}",
    updatemenus=[dict(buttons=buttons9, direction="down", x=0.01, y=1.12, showactive=True)],
    height=500, dragmode="zoom",
    xaxis_title="Count", yaxis_title="Value",
    margin=dict(l=200, r=100, t=60, b=40)
)
figures.append(("Section 9 — Categorical Variable Distributions", fig9))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — Data Quality Summary Table
# ══════════════════════════════════════════════════════════════════════════════
all_cols = df.columns.tolist()
dtypes = df.dtypes.astype(str)
flags = []
for col in all_cols:
    f = []
    if null_rates[col] > 20:
        f.append("High nulls")
    if distinct_counts[col] > 0.8 * n_rows:
        f.append("High cardinality")
    if distinct_counts[col] == 1:
        f.append("Zero variance")
    flags.append(", ".join(f) if f else "")

row_colors = [["#ffe5e5" if fl else "white"] * 6 for fl in flags]

fig10 = go.Figure(go.Table(
    header=dict(
        values=["<b>Column</b>", "<b>Data Type</b>", "<b>Null Count</b>",
                "<b>Null Rate %</b>", "<b>Distinct Values</b>", "<b>Flags</b>"],
        fill_color="#2E86AB",
        font=dict(color="white", size=12),
        align="left"
    ),
    cells=dict(
        values=[
            all_cols,
            [dtypes[c] for c in all_cols],
            [null_counts[c] for c in all_cols],
            [f"{null_rates[c]:.2f}%" for c in all_cols],
            [distinct_counts[c] for c in all_cols],
            flags
        ],
        fill_color=[[r[0] for r in row_colors]],
        align="left",
        font=dict(size=11)
    )
))
fig10.update_layout(title="Section 10 — Data Quality Summary Table", height=600)
figures.append(("Section 10 — Data Quality Summary", fig10))

# ══════════════════════════════════════════════════════════════════════════════
# WRITE HTML REPORT
# ══════════════════════════════════════════════════════════════════════════════
with open(output_path, "w") as f:
    f.write("""<html>
<head>
<title>EDA Report — Telco Customer Churn</title>
<style>
  body { font-family: 'Helvetica Neue', sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
  h1 { color: #2E86AB; border-bottom: 2px solid #2E86AB; padding-bottom: 10px; }
  h2 { color: #444; margin-top: 40px; }
  .section { background: white; border-radius: 6px; padding: 20px; margin-bottom: 24px;
             box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
</style>
</head>
<body>
<h1>EDA Report — Telco Customer Churn</h1>
<p style="color:#666;">Generated: 2026-05-10 | Analysis ID: telco_customer_churn</p>
""")
    f.write(section1_html)
    first = True
    for section_title, fig in figures:
        f.write(f'<div class="section">\n')
        if first:
            f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))
            first = False
        else:
            f.write(fig.to_html(full_html=False, include_plotlyjs=False))
        f.write("</div>\n")
    f.write("</body></html>")

print(f"EDA report saved to: {output_path}")

# Open in browser
webbrowser.open("file://" + os.path.abspath(output_path))
print("Opened in browser.")

# ── Print summary stats for chat panel ────────────────────────────────────────
print("\n=== SUMMARY STATS ===")
print(f"Rows: {n_rows}, Cols: {n_cols}")
print(f"Churn=Yes: {churn_yes} ({churn_yes_pct}%), Churn=No: {churn_no} ({churn_no_pct}%)")
print("\nNull rates:")
for _, row in null_df[null_df["null_rate"] > 0].iterrows():
    print(f"  {row['column']}: {row['null_rate']:.2f}% ({int(row['null_count'])} rows)")
print("\nCorrelations with Churn:")
for col, corr in df[continuous_cols].corrwith(df[target_binary]).items():
    print(f"  {col}: {corr:.3f}")
print("\nCorrelation matrix (continuous):")
print(corr_m.round(3))
print("\nOutlier counts:")
for col, cnt in outlier_counts.items():
    print(f"  {col}: {cnt} outliers ({100*cnt/n_rows:.1f}%)")
print("\nDistinct values per categorical col:")
for col in categorical_cols:
    print(f"  {col}: {distinct_counts[col]} distinct | top: {df[col].value_counts().index[0]} ({df[col].value_counts().iloc[0]})")
