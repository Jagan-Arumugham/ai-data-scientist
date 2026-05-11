import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
import warnings
warnings.filterwarnings("ignore")

# ── Load and apply all EDA encoding decisions ─────────────────────────────────
df = pd.read_csv("analyses/telco_customer_churn/data/WA_Fn-UseC_-Telco-Customer-Churn.csv")

# Fix TotalCharges type (before dropping)
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

# Apply EDA decisions
df.drop(columns=["customerID", "TotalCharges"], inplace=True)

# Recode SeniorCitizen 0/1 → Yes/No
df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})

# Collapse 3-level service columns to Yes/No
three_level_cols = [
    "MultipleLines", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"
]
for col in three_level_cols:
    df[col] = df[col].replace({"No phone service": "No", "No internet service": "No"})

# Segments
churned = df[df["Churn"] == "Yes"]
retained = df[df["Churn"] == "No"]
n_total = len(df)
n_churn = len(churned)
n_retain = len(retained)

continuous_cols = ["tenure", "MonthlyCharges"]
categorical_cols = [
    "gender", "SeniorCitizen", "Partner", "Dependents",
    "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod"
]

# ── Cohen's d for continuous vars ─────────────────────────────────────────────
def cohens_d(g1, g2):
    n1, n2 = len(g1), len(g2)
    pooled_std = np.sqrt(((n1-1)*g1.std()**2 + (n2-1)*g2.std()**2) / (n1+n2-2))
    return (g1.mean() - g2.mean()) / pooled_std if pooled_std > 0 else 0

# ── Cramér's V for categorical vars ──────────────────────────────────────────
def cramers_v(col, target_col, data):
    ct = pd.crosstab(data[col], data[target_col])
    chi2, p, dof, _ = chi2_contingency(ct)
    n = ct.sum().sum()
    r, k = ct.shape
    v = np.sqrt(chi2 / (n * (min(r, k) - 1))) if min(r, k) > 1 else 0
    return v, p

# ── Effect size interpretation ────────────────────────────────────────────────
def interpret_d(d):
    d = abs(d)
    if d >= 0.8: return "LARGE"
    if d >= 0.5: return "MEDIUM"
    if d >= 0.2: return "SMALL"
    return "NEGLIGIBLE"

def interpret_v(v):
    if v >= 0.3: return "STRONG"
    if v >= 0.1: return "MODERATE"
    return "NEGLIGIBLE"

# ── Continuous profiling ──────────────────────────────────────────────────────
print("=" * 70)
print("CONTINUOUS VARIABLE PROFILING")
print("=" * 70)

cont_results = []
for col in continuous_cols:
    pop_mean = df[col].mean()
    pop_med  = df[col].median()
    pop_std  = df[col].std()

    c_mean = churned[col].mean();  c_med = churned[col].median()
    c_std  = churned[col].std();   c_p25 = churned[col].quantile(0.25); c_p75 = churned[col].quantile(0.75)

    r_mean = retained[col].mean(); r_med = retained[col].median()
    r_std  = retained[col].std();  r_p25 = retained[col].quantile(0.25); r_p75 = retained[col].quantile(0.75)

    d = cohens_d(churned[col], retained[col])
    f_stat, p_anova = stats.f_oneway(churned[col], retained[col])

    cont_results.append({
        "variable": col,
        "pop_mean": pop_mean, "pop_med": pop_med, "pop_std": pop_std,
        "churn_mean": c_mean, "churn_med": c_med, "churn_std": c_std,
        "churn_p25": c_p25, "churn_p75": c_p75,
        "retain_mean": r_mean, "retain_med": r_med, "retain_std": r_std,
        "retain_p25": r_p25, "retain_p75": r_p75,
        "cohens_d": d, "effect_label": interpret_d(d),
        "p_anova": p_anova, "sig": p_anova < 0.05
    })

    print(f"\n{col}")
    print(f"  Population : mean={pop_mean:.1f}  median={pop_med:.1f}  std={pop_std:.1f}")
    print(f"  Churned    : mean={c_mean:.1f}  median={c_med:.1f}  std={c_std:.1f}  P25={c_p25:.1f}  P75={c_p75:.1f}")
    print(f"  Retained   : mean={r_mean:.1f}  median={r_med:.1f}  std={r_std:.1f}  P25={r_p25:.1f}  P75={r_p75:.1f}")
    print(f"  Cohen's d  : {d:.3f} ({interpret_d(d)})  |  ANOVA p={p_anova:.2e}  sig={p_anova<0.05}")

# ── Categorical profiling ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("CATEGORICAL VARIABLE PROFILING")
print("=" * 70)

cat_results = []
for col in categorical_cols:
    v, p = cramers_v(col, "Churn", df)
    sig = p < 0.05

    pop_dist = df[col].value_counts(normalize=True).mul(100).round(1)
    churn_dist = churned[col].value_counts(normalize=True).mul(100).round(1)
    retain_dist = retained[col].value_counts(normalize=True).mul(100).round(1)

    # Lift per category
    lifts = {}
    for cat in df[col].unique():
        pop_rate = (df[col] == cat).mean()
        churn_rate = (churned[col] == cat).mean()
        lifts[cat] = churn_rate / pop_rate if pop_rate > 0 else np.nan

    max_lift_cat = max(lifts, key=lambda x: abs(lifts[x] - 1) if not np.isnan(lifts[x]) else 0)
    max_lift = lifts[max_lift_cat]

    cat_results.append({
        "variable": col,
        "cramers_v": v,
        "effect_label": interpret_v(v),
        "p_chi2": p,
        "sig": sig,
        "pop_dist": pop_dist,
        "churn_dist": churn_dist,
        "retain_dist": retain_dist,
        "lifts": lifts,
        "max_lift_cat": max_lift_cat,
        "max_lift": max_lift
    })

    print(f"\n{col}  |  Cramér's V={v:.3f} ({interpret_v(v)})  |  chi2 p={p:.2e}  sig={sig}")
    all_cats = df[col].value_counts().index
    for cat in all_cats:
        pp  = pop_dist.get(cat, 0)
        cp  = churn_dist.get(cat, 0)
        rp  = retain_dist.get(cat, 0)
        lft = lifts.get(cat, np.nan)
        print(f"  {cat:<30}  pop={pp:5.1f}%  churn={cp:5.1f}%  retain={rp:5.1f}%  lift={lft:.2f}")

# ── Rank all variables by effect size ────────────────────────────────────────
print("\n" + "=" * 70)
print("RANKED DIFFERENTIATORS")
print("=" * 70)

ranking = []
for r in cont_results:
    ranking.append({
        "variable": r["variable"],
        "effect_size": abs(r["cohens_d"]),
        "metric": "Cohen's d",
        "effect_label": r["effect_label"],
        "sig": r["sig"],
        "direction": f"Churned mean={r['churn_mean']:.1f} vs Retained mean={r['retain_mean']:.1f}"
    })
for r in cat_results:
    ranking.append({
        "variable": r["variable"],
        "effect_size": r["cramers_v"],
        "metric": "Cramér's V",
        "effect_label": r["effect_label"],
        "sig": r["sig"],
        "direction": f"Highest lift: '{r['max_lift_cat']}' (lift={r['max_lift']:.2f})"
    })

ranking_df = pd.DataFrame(ranking).sort_values("effect_size", ascending=False)
print(ranking_df[["variable","metric","effect_size","effect_label","sig","direction"]].to_string(index=False))

# ── Churn rate by key categorical values ─────────────────────────────────────
print("\n" + "=" * 70)
print("CHURN RATE BY VARIABLE VALUE (top differentiators)")
print("=" * 70)

for col in ["Contract", "InternetService", "PaymentMethod", "tenure", "SeniorCitizen",
            "OnlineSecurity", "TechSupport", "PaperlessBilling", "Partner", "Dependents"]:
    if col in continuous_cols:
        continue
    ct = df.groupby(col)["Churn"].apply(lambda x: (x=="Yes").mean()*100).round(1).sort_values(ascending=False)
    print(f"\n{col} churn rates:")
    for val, rate in ct.items():
        n_val = (df[col] == val).sum()
        print(f"  {val:<35} {rate:5.1f}%  (n={n_val:,})")

# ── Tenure bands ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TENURE BANDS — CHURN RATE")
print("=" * 70)
df["tenure_band"] = pd.cut(df["tenure"], bins=[0,6,12,24,48,72],
                            labels=["0-6m","7-12m","13-24m","25-48m","49-72m"], include_lowest=True)
tb = df.groupby("tenure_band", observed=True)["Churn"].apply(lambda x: (x=="Yes").mean()*100).round(1)
tb_n = df.groupby("tenure_band", observed=True).size()
for band in tb.index:
    print(f"  {band:<10}  churn rate={tb[band]:5.1f}%  n={tb_n[band]:,}")
