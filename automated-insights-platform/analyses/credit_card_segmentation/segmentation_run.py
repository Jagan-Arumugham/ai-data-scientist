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
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA

pio.templates.default = "plotly_white"
COLOR_GROUP_1 = "#2E86AB"
COLOR_GROUP_2 = "#E84855"
COLOR_NEUTRAL = "#6C757D"
COLOR_FLAG_RED = "#E84855"
COLOR_FLAG_AMBER = "#F4A261"
COLOR_FLAG_GREEN = "#2A9D8F"
CLUSTER_PALETTE = ["#2E86AB", "#E84855", "#2A9D8F", "#F4A261", "#9B59B6", "#F39C12", "#1ABC9C", "#E74C3C"]

analysis_id = "credit_card_segmentation"
base_dir = os.path.join("analyses", analysis_id)
data_path = os.path.join(base_dir, "data", "cc_general.csv")
output_dir = os.path.join(base_dir, "outputs")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "segmentation_report.html")

# ============================================================
# LOAD AND APPLY EDA DECISIONS
# ============================================================
df = pd.read_csv(data_path)

# Null imputation per state.json
df['MINIMUM_PAYMENTS'] = df['MINIMUM_PAYMENTS'].fillna(df['MINIMUM_PAYMENTS'].median())
df['CREDIT_LIMIT'] = df['CREDIT_LIMIT'].fillna(df['CREDIT_LIMIT'].median())

# Derived feature
df['BALANCE_TO_LIMIT_RATIO'] = df['BALANCE'] / df['CREDIT_LIMIT']
df['BALANCE_TO_LIMIT_RATIO'] = df['BALANCE_TO_LIMIT_RATIO'].clip(upper=1.0)  # cap at 100% utilization

# Clustering feature set (from state.json columns_retained)
CLUSTER_FEATURES = [
    'BALANCE', 'CREDIT_LIMIT', 'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES',
    'CASH_ADVANCE', 'PAYMENTS', 'MINIMUM_PAYMENTS', 'PURCHASES_TRX',
    'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
    'CASH_ADVANCE_FREQUENCY', 'PRC_FULL_PAYMENT', 'BALANCE_TO_LIMIT_RATIO'
]

X = df[CLUSTER_FEATURES].copy()
n_rows = len(X)

# Z-score standardization
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ============================================================
# K SELECTION — ELBOW + SILHOUETTE (k=2 to k=8)
# ============================================================
K_RANGE = range(2, 9)
inertias = {}
silhouette_scores = {}
db_scores = {}

np.random.seed(42)
print("Running k-means for k=2 to k=8 (n_init=20 each)...")
for k in K_RANGE:
    km = KMeans(n_clusters=k, n_init=20, random_state=42, max_iter=500)
    labels = km.fit_predict(X_scaled)
    inertias[k] = km.inertia_
    silhouette_scores[k] = round(silhouette_score(X_scaled, labels, sample_size=3000, random_state=42), 4)
    db_scores[k] = round(davies_bouldin_score(X_scaled, labels), 4)
    print(f"  k={k}: inertia={inertias[k]:.0f} | silhouette={silhouette_scores[k]:.4f} | DB={db_scores[k]:.4f}")

# ============================================================
# FIT RECOMMENDED K
# ============================================================
best_k = 7  # analyst instruction: re-run at k=7
print(f"\nAnalyst-specified k={best_k} | silhouette={silhouette_scores[best_k]:.4f}")

km_final = KMeans(n_clusters=best_k, n_init=50, random_state=42, max_iter=500)
df['cluster'] = km_final.fit_predict(X_scaled)

# Cluster sizes
cluster_counts = df['cluster'].value_counts().sort_index()
cluster_pcts = (cluster_counts / n_rows * 100).round(1)

# Per-cluster means on original (unstandardized) scale
cluster_means = df.groupby('cluster')[CLUSTER_FEATURES].mean()
cluster_means_z = pd.DataFrame(
    scaler.transform(cluster_means),
    index=cluster_means.index,
    columns=CLUSTER_FEATURES
)

# ============================================================
# PCA FOR 2D VISUALIZATION
# ============================================================
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_scaled)
df['pca_1'] = X_pca[:, 0]
df['pca_2'] = X_pca[:, 1]
pca_var = pca.explained_variance_ratio_

# ============================================================
# PROVISIONAL CLUSTER NAMING (based on dominant characteristics)
# ============================================================
def name_cluster(row, cluster_id):
    """Assign provisional name from cluster profile."""
    high_cash = row['CASH_ADVANCE_FREQUENCY'] > 0.5 or row['CASH_ADVANCE'] > 1500
    high_prc = row['PRC_FULL_PAYMENT'] > 0.4
    low_purchases = row['ONEOFF_PURCHASES'] < 200 and row['INSTALLMENTS_PURCHASES'] < 200
    high_purchases = row['ONEOFF_PURCHASES'] > 800 or row['INSTALLMENTS_PURCHASES'] > 600
    high_balance = row['BALANCE'] > 2000
    low_balance = row['BALANCE'] < 500
    high_purch_trx = row['PURCHASES_TRX'] > 20
    high_installments = row['INSTALLMENTS_PURCHASES'] > row['ONEOFF_PURCHASES'] * 1.5

    if high_cash and not high_purchases:
        return f"Cluster {cluster_id} — Cash Advance Users"
    elif high_prc and high_purchases:
        return f"Cluster {cluster_id} — Active Transactors (Pay in Full)"
    elif high_balance and low_purchases:
        return f"Cluster {cluster_id} — Revolvers (High Balance, Low Purchase)"
    elif low_balance and low_purchases:
        return f"Cluster {cluster_id} — Dormant / Minimal Usage"
    elif high_installments:
        return f"Cluster {cluster_id} — Installment Purchasers"
    elif high_purchases and not high_prc:
        return f"Cluster {cluster_id} — High Spenders (Carry Balance)"
    else:
        return f"Cluster {cluster_id}"

provisional_names = {}
for cid in range(best_k):
    row = cluster_means.loc[cid]
    provisional_names[cid] = name_cluster(row, cid)

# ============================================================
# BUILD HTML REPORT
# ============================================================
sections = []

# --- Section 1: K Selection — Elbow + Silhouette ---
k_list = list(K_RANGE)
fig1 = make_subplots(
    rows=1, cols=3,
    subplot_titles=["Elbow — Within-Cluster Sum of Squares",
                    "Silhouette Score (higher = better)",
                    "Davies-Bouldin Score (lower = better)"],
    horizontal_spacing=0.1
)

fig1.add_trace(go.Scatter(
    x=k_list, y=[inertias[k] for k in k_list],
    mode='lines+markers',
    marker=dict(color=COLOR_GROUP_1, size=8),
    line=dict(color=COLOR_GROUP_1, width=2),
    name='Inertia',
    hovertemplate="k=%{x}<br>Inertia: %{y:,.0f}<extra></extra>"
), row=1, col=1)

fig1.add_trace(go.Scatter(
    x=k_list, y=[silhouette_scores[k] for k in k_list],
    mode='lines+markers',
    marker=dict(color=COLOR_FLAG_GREEN, size=8),
    line=dict(color=COLOR_FLAG_GREEN, width=2),
    name='Silhouette',
    hovertemplate="k=%{x}<br>Silhouette: %{y:.4f}<extra></extra>"
), row=1, col=2)

fig1.add_trace(go.Scatter(
    x=k_list, y=[db_scores[k] for k in k_list],
    mode='lines+markers',
    marker=dict(color=COLOR_GROUP_2, size=8),
    line=dict(color=COLOR_GROUP_2, width=2),
    name='Davies-Bouldin',
    hovertemplate="k=%{x}<br>DB Score: %{y:.4f}<extra></extra>"
), row=1, col=3)

# Mark recommended k
for col_n, y_vals, metric in [
    (1, [inertias[k] for k in k_list], 'Inertia'),
    (2, [silhouette_scores[k] for k in k_list], 'Silhouette'),
    (3, [db_scores[k] for k in k_list], 'DB')
]:
    idx = k_list.index(best_k)
    fig1.add_trace(go.Scatter(
        x=[best_k], y=[y_vals[idx]],
        mode='markers',
        marker=dict(color=COLOR_FLAG_AMBER, size=14, symbol='star'),
        name=f'Recommended k={best_k}',
        showlegend=(col_n == 1),
        hovertemplate=f"★ Recommended k={best_k}<extra></extra>"
    ), row=1, col=col_n)

fig1.update_xaxes(title_text="k", dtick=1)
fig1.update_layout(
    title=f"K Selection Diagnostics — Recommended k={best_k} (★)<br>"
          f"<sup>Silhouette scores: {' | '.join([f'k={k}: {silhouette_scores[k]:.3f}' for k in k_list])}</sup>",
    height=400, dragmode="zoom", showlegend=True
)
sections.append(("fig", f"Section 1 — K Selection Diagnostics", fig1))

# --- Section 2: Cluster Size Distribution ---
colors2 = [CLUSTER_PALETTE[i % len(CLUSTER_PALETTE)] for i in range(best_k)]
fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=[f"Cluster {i}" for i in cluster_counts.index],
    y=cluster_counts.values,
    marker_color=colors2,
    text=[f"{cluster_pcts[i]:.1f}%" for i in cluster_counts.index],
    textposition='outside',
    hovertemplate="Cluster %{x}<br>Count: %{y:,}<br>Share: %{text}<extra></extra>",
    name=''
))
# Flag if any cluster > 50%
if any(p > 50 for p in cluster_pcts):
    max_cluster = cluster_pcts.idxmax()
    fig2.add_annotation(
        text=f"⚠ Cluster {max_cluster} exceeds 50% — may contain sub-groups",
        xref='paper', yref='paper', x=0.5, y=1.08,
        showarrow=False, font=dict(color=COLOR_FLAG_AMBER, size=12)
    )
fig2.update_layout(
    title=f"Cluster Size Distribution — k={best_k}<br>"
          f"<sup>Total population: {n_rows:,} accounts</sup>",
    xaxis_title="Cluster", yaxis_title="Count",
    height=400, dragmode="zoom", showlegend=False
)
sections.append(("fig", "Section 2 — Cluster Size Distribution", fig2))

# --- Section 3: Cluster Profiles — Standardized Mean Heatmap ---
# Show z-scored means per cluster (positive = above average, negative = below)
fig3 = go.Figure(go.Heatmap(
    z=cluster_means_z.values,
    x=CLUSTER_FEATURES,
    y=[f"Cluster {i} (n={cluster_counts[i]:,})" for i in range(best_k)],
    colorscale='RdBu',
    zmid=0,
    text=[[f"{v:.2f}" for v in row] for row in cluster_means_z.values],
    texttemplate="%{text}",
    hovertemplate="<b>Cluster %{y}</b><br><b>%{x}</b><br>Z-score: %{z:.2f}<extra></extra>",
    colorbar=dict(title="Z-score vs<br>Population Mean")
))
fig3.update_layout(
    title=f"Cluster Profiles — Standardized Variable Means (z-score)<br>"
          f"<sup>Blue = below population average | Red = above population average</sup>",
    xaxis=dict(tickangle=45, tickfont=dict(size=10)),
    yaxis=dict(tickfont=dict(size=11)),
    height=max(350, 80 * best_k),
    dragmode="zoom",
    margin=dict(b=150)
)
sections.append(("fig", "Section 3 — Cluster Profiles (Standardized Means)", fig3))

# --- Section 4: Cluster Profiles — Actual Means Table ---
display_cols = ['BALANCE', 'CREDIT_LIMIT', 'BALANCE_TO_LIMIT_RATIO',
                'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES', 'PURCHASES_TRX',
                'CASH_ADVANCE', 'PAYMENTS', 'MINIMUM_PAYMENTS',
                'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
                'CASH_ADVANCE_FREQUENCY', 'PRC_FULL_PAYMENT']
display_cols = [c for c in display_cols if c in cluster_means.columns]

# Format numbers for display
def fmt(val, col):
    if col in ['BALANCE_TO_LIMIT_RATIO', 'PRC_FULL_PAYMENT', 'ONEOFF_PURCHASES_FREQUENCY',
               'PURCHASES_INSTALLMENTS_FREQUENCY', 'CASH_ADVANCE_FREQUENCY']:
        return f"{val:.2f}"
    elif col == 'PURCHASES_TRX':
        return f"{val:.1f}"
    else:
        return f"{val:,.0f}"

header_vals = ['Variable'] + [f"Cluster {i}<br>n={cluster_counts[i]:,}" for i in range(best_k)]
cell_vals = [display_cols]
for i in range(best_k):
    col_data = [fmt(cluster_means.loc[i, c], c) for c in display_cols]
    cell_vals.append(col_data)

# Alternating row colors
alt_colors = [['#f0f7ff' if r % 2 == 0 else 'white' for r in range(len(display_cols))]]
for _ in range(best_k):
    alt_colors.append(['#f0f7ff' if r % 2 == 0 else 'white' for r in range(len(display_cols))])

cluster_colors = [CLUSTER_PALETTE[i % len(CLUSTER_PALETTE)] for i in range(best_k)]

fig4 = go.Figure(go.Table(
    header=dict(
        values=header_vals,
        fill_color=[COLOR_GROUP_1] + cluster_colors,
        font=dict(color='white', size=11),
        align='center', height=30
    ),
    cells=dict(
        values=cell_vals,
        fill_color=alt_colors,
        align=['left'] + ['center'] * best_k,
        font=dict(size=11), height=26
    )
))
fig4.update_layout(
    title="Cluster Profiles — Actual Variable Means",
    height=max(500, 30 * len(display_cols) + 100)
)
sections.append(("fig", "Section 4 — Cluster Profiles (Actual Means)", fig4))

# --- Section 5: PCA Scatter — 2D View of Clusters ---
sample_n = min(3000, n_rows)
sample_idx = np.random.RandomState(42).choice(n_rows, sample_n, replace=False)
df_sample = df.iloc[sample_idx]

fig5 = go.Figure()
for cid in range(best_k):
    mask = df_sample['cluster'] == cid
    subset = df_sample[mask]
    fig5.add_trace(go.Scatter(
        x=subset['pca_1'], y=subset['pca_2'],
        mode='markers',
        marker=dict(color=CLUSTER_PALETTE[cid % len(CLUSTER_PALETTE)], opacity=0.5, size=4),
        name=f"Cluster {cid} (n={cluster_counts[cid]:,})",
        hovertemplate=(
            f"<b>Cluster {cid}</b><br>"
            "PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>"
            f"BALANCE: {cluster_means.loc[cid, 'BALANCE']:,.0f}<br>"
            f"PRC_FULL_PAYMENT: {cluster_means.loc[cid, 'PRC_FULL_PAYMENT']:.2f}<extra></extra>"
        )
    ))
fig5.update_layout(
    title=f"PCA Scatter — Cluster Separation (2D Projection)<br>"
          f"<sup>PC1 explains {pca_var[0]*100:.1f}% variance | PC2 explains {pca_var[1]*100:.1f}% | "
          f"Combined: {sum(pca_var)*100:.1f}% | Sampled to {sample_n:,} points</sup>",
    xaxis_title=f"PC1 ({pca_var[0]*100:.1f}% variance explained)",
    yaxis_title=f"PC2 ({pca_var[1]*100:.1f}% variance explained)",
    height=550, dragmode="select",
    legend=dict(orientation='v', x=1.02, y=0.5)
)
sections.append(("fig", "Section 5 — PCA Scatter Plot (Cluster Separation)", fig5))

# --- Section 6: Key Variable Distributions by Cluster ---
key_profile_vars = ['BALANCE', 'PRC_FULL_PAYMENT', 'CASH_ADVANCE_FREQUENCY',
                    'ONEOFF_PURCHASES', 'PURCHASES_INSTALLMENTS_FREQUENCY']
key_profile_vars = [v for v in key_profile_vars if v in df.columns]

fig6 = make_subplots(
    rows=1, cols=len(key_profile_vars),
    subplot_titles=key_profile_vars,
    horizontal_spacing=0.08
)
for col_n, var in enumerate(key_profile_vars):
    for cid in range(best_k):
        vals = df[df['cluster'] == cid][var]
        fig6.add_trace(go.Box(
            y=vals, name=f"C{cid}",
            marker_color=CLUSTER_PALETTE[cid % len(CLUSTER_PALETTE)],
            line_color=CLUSTER_PALETTE[cid % len(CLUSTER_PALETTE)],
            boxpoints=False,
            showlegend=(col_n == 0),
            hovertemplate=f"Cluster {cid}<br>{var}<br>Median: %{{median:.2f}}<extra></extra>"
        ), row=1, col=col_n + 1)

fig6.update_layout(
    title="Key Variable Distributions by Cluster<br>"
          "<sup>Box plots show median and IQR per cluster per variable</sup>",
    height=500, dragmode="zoom"
)
sections.append(("fig", "Section 6 — Key Variable Distributions by Cluster", fig6))

# ============================================================
# WRITE HTML REPORT
# ============================================================
style = """
<style>
body{font-family:Arial,sans-serif;max-width:1400px;margin:0 auto;padding:20px;background:#f5f7fa}
h1{color:#2E86AB;border-bottom:3px solid #2E86AB;padding-bottom:10px}
h2{color:#1a5c7a;border-bottom:1px solid #cce0ec;padding-bottom:6px;margin-top:40px;font-size:1.1em}
.summary-card{background:white;border-radius:8px;padding:20px;margin:10px 0;box-shadow:0 1px 4px rgba(0,0,0,0.1)}
.cluster-badge{display:inline-block;padding:4px 10px;border-radius:4px;color:white;font-weight:bold;margin:3px}
</style>
"""

with open(output_path, "w") as f:
    f.write(f"<html><head><title>Segmentation — Credit Card</title>{style}</head><body>\n")
    f.write(f"<h1>Segmentation Report — Credit Card Customer Segmentation</h1>\n")
    f.write(f"<p style='color:gray'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
            f"k={best_k} clusters | {n_rows:,} accounts</p>\n")

    # Summary card
    badges = ''.join([f"<span class='cluster-badge' style='background:{CLUSTER_PALETTE[i % len(CLUSTER_PALETTE)]}'>"
                      f"Cluster {i}: {cluster_counts[i]:,} ({cluster_pcts[i]:.1f}%)</span>"
                      for i in range(best_k)])
    sil_summary = ' | '.join([f"k={k}: {silhouette_scores[k]:.3f}" for k in k_list])

    size_flag = ""
    if any(p > 50 for p in cluster_pcts):
        max_cid = cluster_pcts.idxmax()
        size_flag = f"<p style='color:{COLOR_FLAG_AMBER}'>⚠ Cluster {max_cid} ({cluster_pcts[max_cid]:.1f}%) exceeds 50% of population — review for sub-groups</p>"

    f.write(f"""
    <div class='summary-card'>
        <h3 style='margin-top:0;color:#2E86AB'>Segmentation Summary</h3>
        <p><strong>Approach:</strong> K-Means clustering (unsupervised) — no target variable defined</p>
        <p><strong>Features used:</strong> {len(CLUSTER_FEATURES)} variables after EDA exclusions + BALANCE_TO_LIMIT_RATIO derived feature</p>
        <p><strong>Recommended k:</strong> {best_k} (highest silhouette score: {silhouette_scores[best_k]:.4f})</p>
        <p><strong>Silhouette scores by k:</strong> {sil_summary}</p>
        <p><strong>Cluster sizes:</strong><br>{badges}</p>
        {size_flag}
    </div>
    """)

    first_plotly = True
    for sec_type, sec_title, content in sections:
        f.write(f"<h2>{sec_title}</h2>\n")
        include_js = "cdn" if first_plotly else False
        f.write(content.to_html(full_html=False, include_plotlyjs=include_js) + "\n")
        first_plotly = False

    f.write("</body></html>")

print(f"[OK] Segmentation report saved: {output_path}")
webbrowser.open("file://" + os.path.abspath(output_path))
print("[OK] Report opened in browser.")

# ============================================================
# PRINT SUMMARY FOR CHAT
# ============================================================
print("\n" + "=" * 65)
print("SEGMENTATION SUMMARY")
print("=" * 65)
print(f"k evaluated: 2–8 | Recommended: k={best_k}")
print(f"\nSilhouette scores:")
for k in k_list:
    marker = " ← recommended" if k == best_k else ""
    print(f"  k={k}: silhouette={silhouette_scores[k]:.4f} | DB={db_scores[k]:.4f}{marker}")

print(f"\nCluster sizes:")
for cid in range(best_k):
    print(f"  Cluster {cid}: {cluster_counts[cid]:,} accounts ({cluster_pcts[cid]:.1f}%)")

print(f"\nCluster profiles (key variables):")
key_show = ['BALANCE', 'CREDIT_LIMIT', 'BALANCE_TO_LIMIT_RATIO',
            'ONEOFF_PURCHASES', 'INSTALLMENTS_PURCHASES', 'CASH_ADVANCE',
            'PRC_FULL_PAYMENT', 'CASH_ADVANCE_FREQUENCY',
            'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
            'PAYMENTS', 'PURCHASES_TRX']
key_show = [c for c in key_show if c in cluster_means.columns]

header = f"{'Variable':<38}" + "".join([f"{'C'+str(i):>12}" for i in range(best_k)])
print(header)
print("-" * (38 + 12 * best_k))
for col in key_show:
    row_str = f"{col:<38}"
    for cid in range(best_k):
        val = cluster_means.loc[cid, col]
        if col in ['BALANCE_TO_LIMIT_RATIO', 'PRC_FULL_PAYMENT',
                   'ONEOFF_PURCHASES_FREQUENCY', 'PURCHASES_INSTALLMENTS_FREQUENCY',
                   'CASH_ADVANCE_FREQUENCY']:
            row_str += f"{val:>12.2f}"
        elif col == 'PURCHASES_TRX':
            row_str += f"{val:>12.1f}"
        else:
            row_str += f"{val:>12,.0f}"
    print(row_str)

print(f"\nProvisional names (for analyst review):")
for cid, name in provisional_names.items():
    print(f"  {name} — n={cluster_counts[cid]:,} ({cluster_pcts[cid]:.1f}%)")

print(f"\nPCA variance explained: PC1={pca_var[0]*100:.1f}% | PC2={pca_var[1]*100:.1f}% | Total={sum(pca_var)*100:.1f}%")
