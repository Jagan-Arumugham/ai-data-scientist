import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score, classification_report)
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

# ── Load and apply all prior decisions ────────────────────────────────────────
df = pd.read_csv("analyses/telco_customer_churn/data/WA_Fn-UseC_-Telco-Customer-Churn.csv")
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df.drop(columns=["customerID", "TotalCharges"], inplace=True)
df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})
for col in ["MultipleLines", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
            "TechSupport", "StreamingTV", "StreamingMovies"]:
    df[col] = df[col].replace({"No phone service": "No", "No internet service": "No"})

# Drop the 11 rows where MonthlyCharges could be null (TotalCharges was the null — not an issue)
df = df.dropna()

target = "Churn"
y = (df[target] == "Yes").astype(int)

# ── One-hot encode all categorical features ───────────────────────────────────
feature_cols = [c for c in df.columns if c != target]
X = pd.get_dummies(df[feature_cols], drop_first=False)

print(f"Features after encoding: {X.shape[1]}")
print(f"Feature names: {list(X.columns)}\n")

# ── Train/validation split ────────────────────────────────────────────────────
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train):,}  |  Validation: {len(X_val):,}")
print(f"Train churn rate: {y_train.mean()*100:.1f}%  |  Val churn rate: {y_val.mean()*100:.1f}%\n")

# ══════════════════════════════════════════════════════════════════════════════
# MODEL 1 — DECISION TREE (interpretability)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("MODEL 1 — DECISION TREE (depth=4)")
print("=" * 70)

dt = DecisionTreeClassifier(
    max_depth=4,
    min_samples_leaf=max(50, int(0.01 * len(X_train))),
    criterion="gini",
    random_state=42
)
dt.fit(X_train, y_train)
y_pred_dt = dt.predict(X_val)
y_prob_dt = dt.predict_proba(X_val)[:, 1]

auc_dt = roc_auc_score(y_val, y_prob_dt)
f1_dt  = f1_score(y_val, y_pred_dt)
print(f"AUC-ROC : {auc_dt:.4f}")
print(f"F1      : {f1_dt:.4f}")
print(f"Accuracy: {accuracy_score(y_val, y_pred_dt):.4f}")
print(f"Precision: {precision_score(y_val, y_pred_dt):.4f}")
print(f"Recall  : {recall_score(y_val, y_pred_dt):.4f}")

print("\n-- Decision Tree Feature Importances (non-zero) --")
dt_imp = pd.Series(dt.feature_importances_, index=X.columns).sort_values(ascending=False)
dt_imp_nonzero = dt_imp[dt_imp > 0]
for feat, imp in dt_imp_nonzero.items():
    print(f"  {feat:<45}  {imp:.4f}")

print("\n-- Tree Structure (plain text) --")
print(export_text(dt, feature_names=list(X.columns), max_depth=4))

# ══════════════════════════════════════════════════════════════════════════════
# MODEL 2 — GRADIENT BOOSTING + SHAP (robust feature importance)
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("MODEL 2 — GRADIENT BOOSTING")
print("=" * 70)

gb = GradientBoostingClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    random_state=42
)
gb.fit(X_train, y_train)
y_pred_gb = gb.predict(X_val)
y_prob_gb = gb.predict_proba(X_val)[:, 1]

auc_gb = roc_auc_score(y_val, y_prob_gb)
f1_gb  = f1_score(y_val, y_pred_gb)
print(f"AUC-ROC : {auc_gb:.4f}")
print(f"F1      : {f1_gb:.4f}")
print(f"Accuracy: {accuracy_score(y_val, y_pred_gb):.4f}")
print(f"Precision: {precision_score(y_val, y_pred_gb):.4f}")
print(f"Recall  : {recall_score(y_val, y_pred_gb):.4f}")

print("\n-- Gradient Boosting Feature Importances (all, ranked) --")
gb_imp = pd.Series(gb.feature_importances_, index=X.columns).sort_values(ascending=False)
for feat, imp in gb_imp.items():
    bar = "█" * int(imp * 200)
    print(f"  {feat:<45}  {imp:.4f}  {bar}")

# Try SHAP — graceful fallback if not installed
print("\n-- SHAP Values --")
try:
    import shap
    explainer = shap.TreeExplainer(gb)
    shap_values = explainer.shap_values(X_val)
    mean_abs_shap = pd.Series(
        np.abs(shap_values).mean(axis=0), index=X.columns
    ).sort_values(ascending=False)
    print("Mean absolute SHAP values (ranked):")
    for feat, sv in mean_abs_shap.items():
        bar = "█" * int(sv * 500)
        print(f"  {feat:<45}  {sv:.4f}  {bar}")
    shap_available = True
except ImportError:
    print("SHAP not installed — using gradient boosting feature importances as proxy")
    mean_abs_shap = gb_imp
    shap_available = False

# ══════════════════════════════════════════════════════════════════════════════
# MODEL 3 — LOGISTIC REGRESSION (odds ratios)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("MODEL 3 — LOGISTIC REGRESSION (odds ratios)")
print("=" * 70)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc   = scaler.transform(X_val)

lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
lr.fit(X_train_sc, y_train)
y_pred_lr = lr.predict(X_val_sc)
y_prob_lr = lr.predict_proba(X_val_sc)[:, 1]

auc_lr = roc_auc_score(y_val, y_prob_lr)
f1_lr  = f1_score(y_val, y_pred_lr)
print(f"AUC-ROC : {auc_lr:.4f}")
print(f"F1      : {f1_lr:.4f}")

lr_coefs = pd.Series(lr.coef_[0], index=X.columns)
lr_odds  = np.exp(lr_coefs).sort_values(ascending=False)
print("\n-- Odds Ratios (standardised coefficients, ranked descending) --")
print("  [OR > 1 → increases churn odds | OR < 1 → decreases churn odds]")
for feat, odds in lr_odds.items():
    direction = "↑ churn" if odds > 1 else "↓ churn"
    print(f"  {feat:<45}  OR={odds:.3f}  {direction}")

# ══════════════════════════════════════════════════════════════════════════════
# CONSOLIDATED RANKING — average normalised rank across models
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("CONSOLIDATED DRIVER RANKING (avg normalised importance across 3 models)")
print("=" * 70)

def normalise(s):
    mn, mx = s.min(), s.max()
    return (s - mn) / (mx - mn) if mx > mn else s * 0

dt_norm  = normalise(dt_imp)
gb_norm  = normalise(gb_imp)
shap_norm = normalise(mean_abs_shap)
lr_norm  = normalise(lr_coefs.abs())

consolidated = pd.DataFrame({
    "DT": dt_norm,
    "GB": gb_norm,
    "SHAP": shap_norm,
    "LR": lr_norm
}).mean(axis=1).sort_values(ascending=False)

print(f"\n{'Rank':<6}{'Feature':<45}{'Avg Score':>10}  {'DT':>6}  {'GB':>6}  {'LR OR':>8}")
print("-" * 85)
for rank, (feat, score) in enumerate(consolidated.items(), 1):
    odds = lr_odds.get(feat, np.nan)
    print(f"  {rank:<4}{feat:<45}{score:>10.4f}  "
          f"{dt_imp.get(feat,0):>6.4f}  "
          f"{gb_imp.get(feat,0):>6.4f}  "
          f"OR={odds:>5.3f}")

# ══════════════════════════════════════════════════════════════════════════════
# NEAR-ZERO IMPORTANCE — what the model effectively dropped
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("NEAR-ZERO IMPORTANCE (consolidated score < 0.05)")
print("=" * 70)
bottom = consolidated[consolidated < 0.05]
print(f"  {list(bottom.index)}")

# ══════════════════════════════════════════════════════════════════════════════
# DECISION TREE — terminal node analysis
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("DECISION TREE — TERMINAL NODE PROFILES")
print("=" * 70)
leaf_ids = dt.apply(X_val)
val_df = X_val.copy()
val_df["leaf"] = leaf_ids
val_df["actual_churn"] = y_val.values
val_df["pred_prob"] = y_prob_dt

leaf_summary = val_df.groupby("leaf").agg(
    n=("actual_churn", "count"),
    churn_rate=("actual_churn", "mean"),
    avg_prob=("pred_prob", "mean")
).sort_values("churn_rate", ascending=False)
leaf_summary["pct_of_pop"] = (leaf_summary["n"] / len(val_df) * 100).round(1)
leaf_summary["churn_rate_pct"] = (leaf_summary["churn_rate"] * 100).round(1)
print(leaf_summary[["n","pct_of_pop","churn_rate_pct","avg_prob"]].to_string())
