import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import os
import webbrowser
from datetime import datetime

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

pio.templates.default = "plotly_white"
COLOR_GROUP_1 = "#2E86AB"
COLOR_GROUP_2 = "#E84855"
COLOR_NEUTRAL = "#6C757D"
COLOR_FLAG_RED = "#E84855"
COLOR_FLAG_AMBER = "#F4A261"
COLOR_FLAG_GREEN = "#2A9D8F"
CLUSTER_PALETTE = ["#2E86AB", "#E84855", "#2A9D8F", "#F4A261", "#9B59B6"]

analysis_id = "credit_card_segmentation"
base_dir = os.path.join("analyses", analysis_id)
data_path = os.path.join(base_dir, "data", "cc_general.csv")
output_dir = os.path.join(base_dir, "outputs")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "segmentation_final.html")
assignments_path = os.path.join(output_dir, "segment_assignments.csv")

# ============================================================
# LOAD AND APPLY EDA DECISIONS
# ============================================================
df = pd.read_csv(data_path)
df['MINIMUM_PAYMENTS'] = df['MINIMUM_PAYMENTS'].fillna(df['MINIMUM_PAYMENTS'].median())
df['CREDIT_LIMIT'] = df['CREDIT_LIMIT'].fillna(df['CREDIT_LIMIT'].median())
df['BALANCE_TO_LIMIT_RATIO'] = (df['BALANCE'] / df['CREDIT_LIMIT']).clip(upper=1.0)

CLUSTER_FEATURES = [
    'BALANCE', 'CREDIT_LIMIT', 'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES',
    'CASH_ADVANCE', 'PAYMENTS', 'MINIMUM_PAYMENTS', 'PURCHASES_TRX',
    'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
    'CASH_ADVANCE_FREQUENCY', 'PRC_FULL_PAYMENT', 'BALANCE_TO_LIMIT_RATIO'
]

X = df[CLUSTER_FEATURES].copy()
n_rows = len(X)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ============================================================
# FIT k=7
# ============================================================
print("Fitting k=7 (n_init=50)...")
km = KMeans(n_clusters=7, n_init=50, random_state=42, max_iter=500)
raw_labels = km.fit_predict(X_scaled)
df['cluster_raw'] = raw_labels

sil = silhouette_score(X_scaled, raw_labels, sample_size=3000, random_state=42)
print(f"k=7 silhouette: {sil:.4f}")

# ============================================================
# MERGE: C0 → C1 (both are high-utilization revolvers)
#        C5 → C4 (both are high-volume purchasers/VIP)
# ============================================================
merge_map = {0: 1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 6}
df['cluster_merged'] = df['cluster_raw'].map(merge_map)

# Remap to contiguous 0-4
remap = {1: 0, 2: 1, 3: 2, 4: 3, 6: 4}
df['segment'] = df['cluster_merged'].map(remap)

# Provisional names — ordered by segment id after remap
SEGMENT_NAMES = {
    0: "High-Utilization Revolvers",
    1: "Low-Balance Occasional Users",
    2: "Full-Payment Transactors",
    3: "Active Purchasers",
    4: "Cash Advance Revolvers"
}
df['segment_name'] = df['segment'].map(SEGMENT_NAMES)

# ============================================================
# PROFILE MERGED SEGMENTS
# ============================================================
seg_counts = df['segment'].value_counts().sort_index()
seg_pcts = (seg_counts / n_rows * 100).round(1)

profile_cols = CLUSTER_FEATURES + ['BALANCE_FREQUENCY', 'TENURE', 'PURCHASES_FREQUENCY',
                                     'CASH_ADVANCE_TRX', 'PURCHASES']
profile_cols = [c for c in profile_cols if c in df.columns]

seg_means = df.groupby('segment')[profile_cols].mean()
seg_means_z = pd.DataFrame(
    scaler.transform(df.groupby('segment')[CLUSTER_FEATURES].mean()),
    index=seg_means.index, columns=CLUSTER_FEATURES
)

# ============================================================
# PCA
# ============================================================
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_scaled)
df['pca_1'] = X_pca[:, 0]
df['pca_2'] = X_pca[:, 1]
pca_var = pca.explained_variance_ratio_

# ============================================================
# BUILD REPORT
# ============================================================
sections = []

# --- Section 1: Segment Sizes ---
fig1 = go.Figure()
seg_labels = [f"{SEGMENT_NAMES[i]}" for i in seg_counts.index]
fig1.add_trace(go.Bar(
    x=seg_labels,
    y=seg_counts.values,
    marker_color=CLUSTER_PALETTE,
    text=[f"{seg_pcts[i]:.1f}%  (n={seg_counts[i]:,})" for i in seg_counts.index],
    textposition='outside',
    hovertemplate="%{x}<br>Count: %{y:,}<br>Share: %{text}<extra></extra>",
    name=''
))
fig1.update_layout(
    title=f"Final Segment Sizes — k=7 with C0→C1 and C5→C4 merges<br>"
          f"<sup>Total: {n_rows:,} accounts | Silhouette (pre-merge k=7): {sil:.4f}</sup>",
    xaxis_title="Segment", yaxis_title="Count",
    height=450, dragmode="zoom", showlegend=False,
    xaxis=dict(tickangle=-15)
)
sections.append(("fig", "Section 1 — Final Segment Sizes", fig1))

# --- Section 2: Standardized Profile Heatmap ---
seg_means_z_display = pd.DataFrame(
    scaler.transform(df.groupby('segment')[CLUSTER_FEATURES].mean()),
    columns=CLUSTER_FEATURES
)
fig2 = go.Figure(go.Heatmap(
    z=seg_means_z_display.values,
    x=CLUSTER_FEATURES,
    y=[f"{SEGMENT_NAMES[i]}<br>(n={seg_counts[i]:,})" for i in range(5)],
    colorscale='RdBu', zmid=0,
    text=[[f"{v:.2f}" for v in row] for row in seg_means_z_display.values],
    texttemplate="%{text}",
    hovertemplate="<b>%{y}</b><br><b>%{x}</b><br>Z-score: %{z:.2f}<extra></extra>",
    colorbar=dict(title="Z-score")
))
fig2.update_layout(
    title="Segment Profiles — Standardized Variable Means<br>"
          "<sup>Red = above average | Blue = below average</sup>",
    xaxis=dict(tickangle=45, tickfont=dict(size=10)),
    height=420, dragmode="zoom", margin=dict(b=150, l=250)
)
sections.append(("fig", "Section 2 — Segment Profiles (Standardized)", fig2))

# --- Section 3: Actual Means Table ---
display_cols = ['BALANCE', 'CREDIT_LIMIT', 'BALANCE_TO_LIMIT_RATIO',
                'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES', 'PURCHASES_TRX',
                'CASH_ADVANCE', 'CASH_ADVANCE_FREQUENCY',
                'PAYMENTS', 'MINIMUM_PAYMENTS',
                'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
                'PRC_FULL_PAYMENT']
display_cols = [c for c in display_cols if c in seg_means.columns]

def fmt(val, col):
    if col in ['BALANCE_TO_LIMIT_RATIO', 'PRC_FULL_PAYMENT', 'ONEOFF_PURCHASES_FREQUENCY',
               'PURCHASES_INSTALLMENTS_FREQUENCY', 'CASH_ADVANCE_FREQUENCY']:
        return f"{val:.2f}"
    elif col == 'PURCHASES_TRX':
        return f"{val:.1f}"
    else:
        return f"${val:,.0f}"

header_vals = ['Variable'] + [f"{SEGMENT_NAMES[i]}<br>n={seg_counts[i]:,}" for i in range(5)]
cell_vals = [display_cols]
for i in range(5):
    cell_vals.append([fmt(seg_means.loc[i, c], c) for c in display_cols])

alt_colors = [['#f0f7ff' if r % 2 == 0 else 'white' for r in range(len(display_cols))]] * 6

fig3 = go.Figure(go.Table(
    header=dict(
        values=header_vals,
        fill_color=[COLOR_GROUP_1] + CLUSTER_PALETTE,
        font=dict(color='white', size=10), align='center', height=36
    ),
    cells=dict(
        values=cell_vals,
        fill_color=alt_colors,
        align=['left'] + ['center'] * 5,
        font=dict(size=11), height=28
    )
))
fig3.update_layout(
    title="Segment Profiles — Actual Variable Means",
    height=max(550, 30 * len(display_cols) + 100)
)
sections.append(("fig", "Section 3 — Segment Profiles (Actual Means)", fig3))

# --- Section 4: PCA Scatter ---
sample_idx = np.random.RandomState(42).choice(n_rows, min(3000, n_rows), replace=False)
df_s = df.iloc[sample_idx]

fig4 = go.Figure()
for sid in range(5):
    mask = df_s['segment'] == sid
    subset = df_s[mask]
    fig4.add_trace(go.Scatter(
        x=subset['pca_1'], y=subset['pca_2'],
        mode='markers',
        marker=dict(color=CLUSTER_PALETTE[sid], opacity=0.5, size=4),
        name=f"{SEGMENT_NAMES[sid]} (n={seg_counts[sid]:,})",
        hovertemplate=(
            f"<b>{SEGMENT_NAMES[sid]}</b><br>"
            "PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>"
        )
    ))
fig4.update_layout(
    title=f"PCA Scatter — Segment Separation<br>"
          f"<sup>PC1: {pca_var[0]*100:.1f}% | PC2: {pca_var[1]*100:.1f}% | "
          f"Combined: {sum(pca_var)*100:.1f}% | Sampled to {min(3000,n_rows):,} points</sup>",
    xaxis_title=f"PC1 ({pca_var[0]*100:.1f}%)",
    yaxis_title=f"PC2 ({pca_var[1]*100:.1f}%)",
    height=550, dragmode="select",
    legend=dict(orientation='v', x=1.02, y=0.5)
)
sections.append(("fig", "Section 4 — PCA Scatter (Segment Separation)", fig4))

# --- Section 5: Key Variable Box Plots ---
key_vars = ['BALANCE', 'PRC_FULL_PAYMENT', 'CASH_ADVANCE_FREQUENCY',
            'BALANCE_TO_LIMIT_RATIO', 'PURCHASES_TRX']

fig5 = make_subplots(rows=1, cols=len(key_vars),
                     subplot_titles=key_vars, horizontal_spacing=0.07)
for col_n, var in enumerate(key_vars):
    for sid in range(5):
        vals = df[df['segment'] == sid][var]
        fig5.add_trace(go.Box(
            y=vals, name=SEGMENT_NAMES[sid],
            marker_color=CLUSTER_PALETTE[sid],
            line_color=CLUSTER_PALETTE[sid],
            boxpoints=False,
            showlegend=(col_n == 0),
            hovertemplate=f"<b>{SEGMENT_NAMES[sid]}</b><br>Median: %{{median:.2f}}<extra></extra>"
        ), row=1, col=col_n + 1)
fig5.update_layout(
    title="Key Variable Distributions by Segment",
    height=500, dragmode="zoom"
)
sections.append(("fig", "Section 5 — Key Variable Distributions by Segment", fig5))

# ============================================================
# WRITE HTML
# ============================================================
style = """
<style>
body{font-family:Arial,sans-serif;max-width:1450px;margin:0 auto;padding:20px;background:#f5f7fa}
h1{color:#2E86AB;border-bottom:3px solid #2E86AB;padding-bottom:10px}
h2{color:#1a5c7a;border-bottom:1px solid #cce0ec;padding-bottom:6px;margin-top:40px;font-size:1.1em}
.seg-card{display:inline-block;padding:10px 16px;border-radius:6px;color:white;font-weight:bold;margin:4px;font-size:13px}
.summary-card{background:white;border-radius:8px;padding:20px;margin:10px 0;box-shadow:0 1px 4px rgba(0,0,0,0.1)}
</style>
"""

with open(output_path, "w") as f:
    f.write(f"<html><head><title>Final Segmentation — Credit Card</title>{style}</head><body>\n")
    f.write(f"<h1>Final Segmentation — Credit Card Customer Segmentation</h1>\n")
    f.write(f"<p style='color:gray'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
            f"k=7 base with C0→C1 and C5→C4 merges | {n_rows:,} accounts</p>\n")

    badges = ''.join([
        f"<span class='seg-card' style='background:{CLUSTER_PALETTE[i]}'>"
        f"{SEGMENT_NAMES[i]}: {seg_counts[i]:,} ({seg_pcts[i]:.1f}%)</span>"
        for i in range(5)
    ])
    f.write(f"<div class='summary-card'>"
            f"<h3 style='margin-top:0;color:#2E86AB'>5 Final Segments</h3>"
            f"{badges}</div>\n")

    first_plotly = True
    for sec_type, sec_title, content in sections:
        f.write(f"<h2>{sec_title}</h2>\n")
        include_js = "cdn" if first_plotly else False
        f.write(content.to_html(full_html=False, include_plotlyjs=include_js) + "\n")
        first_plotly = False

    f.write("</body></html>")

print(f"[OK] Final segmentation report: {output_path}")
webbrowser.open("file://" + os.path.abspath(output_path))

# ============================================================
# SAVE SEGMENT ASSIGNMENTS
# ============================================================
out_df = df[['CUST_ID', 'segment', 'segment_name'] + CLUSTER_FEATURES].copy()
out_df.to_csv(assignments_path, index=False)
print(f"[OK] Segment assignments saved: {assignments_path}")

# ============================================================
# PRINT FINAL SUMMARY
# ============================================================
print("\n" + "=" * 65)
print("FINAL SEGMENTATION — 5 SEGMENTS (k=7 base, 2 merges applied)")
print("=" * 65)
for sid in range(5):
    print(f"\n  Segment {sid}: {SEGMENT_NAMES[sid]}")
    print(f"    n={seg_counts[sid]:,} ({seg_pcts[sid]:.1f}%)")

print(f"\nFull profiles:")
key_show = ['BALANCE', 'CREDIT_LIMIT', 'BALANCE_TO_LIMIT_RATIO',
            'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES', 'CASH_ADVANCE',
            'PRC_FULL_PAYMENT', 'CASH_ADVANCE_FREQUENCY',
            'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
            'PAYMENTS', 'PURCHASES_TRX']
key_show = [c for c in key_show if c in seg_means.columns]

header = f"{'Variable':<40}" + "".join([f"{'S'+str(i):>12}" for i in range(5)])
print(header)
print("-" * (40 + 12 * 5))
for col in key_show:
    row_str = f"{col:<40}"
    for sid in range(5):
        val = seg_means.loc[sid, col]
        if col in ['BALANCE_TO_LIMIT_RATIO', 'PRC_FULL_PAYMENT',
                   'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
                   'CASH_ADVANCE_FREQUENCY']:
            row_str += f"{val:>12.2f}"
        elif col == 'PURCHASES_TRX':
            row_str += f"{val:>12.1f}"
        else:
            row_str += f"{val:>12,.0f}"
    print(row_str)
