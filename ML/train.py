"""
Build a simple, broad, pipeline to handle athlete's data and trains a model.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve

BASE_DIR = Path(__file__).resolve().parent

# 1. Load data
df = pd.read_csv(BASE_DIR / "synthetic_data.csv")

y = df["injured"]
ids = df["athlete_id"]
X = df.drop(columns=["injured", "day"])  # keep athlete_id in X for now, for grouped imputation

# 2. Grouped train/test split -- entire athletes go to one side or the other
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=ids))

X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
y_train, y_test = y.iloc[train_idx].copy(), y.iloc[test_idx].copy()

print(f"Train rows: {len(X_train)}  |  Test rows: {len(X_test)}")
print(f"Train athletes: {X_train['athlete_id'].nunique()}  |  Test athletes: {X_test['athlete_id'].nunique()}")
assert set(X_train["athlete_id"]) & set(X_test["athlete_id"]) == set(), "Athlete leakage between train/test!"

numeric_cols = X_train.select_dtypes(include="number").columns.tolist()
numeric_cols = [c for c in numeric_cols if c != "athlete_id"]  # id is not a feature
categorical_cols = X_train.select_dtypes(include="object").columns.tolist()

# columns where we know real-world physiological bounds; used for outlier handling
BOUNDS = {
    "avg_hr": (40, 220),
    "speed_kmh": (0, 25),      
    "duration_min": (0, None),
    "rpe": (0, 10)
}

def per_athlete_mean_fill(frame: pd.DataFrame, col: str) -> pd.Series:
    """Fill NaNs with each athlete's own mean for that column; fall back to
    the global mean if an athlete has no valid values at all for it."""
    group_mean = frame.groupby("athlete_id")[col].transform("mean")
    global_mean = frame[col].mean()
    filled = frame[col].fillna(group_mean)
    filled = filled.fillna(global_mean)  # covers the "athlete has zero valid values" edge case
    return filled


def per_athlete_mode_fill(frame: pd.DataFrame, col: str) -> pd.Series:
    """Fill NaNs with each athlete's own most frequent value for that column."""
    def mode_or_na(s: pd.Series):
        m = s.mode()
        return m.iloc[0] if not m.empty else np.nan

    group_mode = frame.groupby("athlete_id")[col].transform(mode_or_na)
    global_mode = frame[col].mode().iloc[0] if not frame[col].mode().empty else "unknown"
    filled = frame[col].fillna(group_mode)
    filled = filled.fillna(global_mode)
    return filled


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()

    # missing values 
    for col in numeric_cols:
        if frame[col].isna().any():
            frame[col] = per_athlete_mean_fill(frame, col)
    for col in categorical_cols:
        if frame[col].isna().any():
            frame[col] = per_athlete_mode_fill(frame, col)

    # outliers: replace implausible values with the athlete's own mean
    for col, (low, high) in BOUNDS.items():
        mask = pd.Series(False, index=frame.index)
        if low is not None:
            mask |= frame[col] < low
        if high is not None:
            mask |= frame[col] > high
        if mask.any():
            replacement = frame.groupby("athlete_id")[col].transform("mean")
            frame.loc[mask, col] = replacement[mask]

    return frame

X_train = clean(X_train) # remove outliers and Nans
X_test = clean(X_test)

# 4. One-hot encode categorical columns (session_type)
ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
train_encoded = ohe.fit_transform(X_train[categorical_cols])
test_encoded = ohe.transform(X_test[categorical_cols])

encoded_cols = ohe.get_feature_names_out(categorical_cols)
train_encoded_df = pd.DataFrame(train_encoded, columns=encoded_cols, index=X_train.index)
test_encoded_df = pd.DataFrame(test_encoded, columns=encoded_cols, index=X_test.index)

# drop original categorical + athlete_id (not a feature) then attach encoded columns
X_train_final = pd.concat(
    [X_train.drop(columns=categorical_cols + ["athlete_id"]), train_encoded_df], axis=1
)
X_test_final = pd.concat(
    [X_test.drop(columns=categorical_cols + ["athlete_id"]), test_encoded_df], axis=1
)

# Train model
model = RandomForestClassifier(n_estimators=300, max_depth=8, class_weight="balanced", random_state=42) # possibly overfitting given the side of the df
model.fit(X_train_final, y_train)

# Evaluate model
proba = model.predict_proba(X_test_final)[:, 1]
preds = (proba >= 0.5).astype(int)

print("\n--- Evaluation ---")
print(classification_report(y_test, preds, digits=3))
print(f"ROC-AUC: {roc_auc_score(y_test, proba):.3f}")

precisions, recalls, thresholds = precision_recall_curve(y_test, proba)
print("\nFeature importances:")
for name, imp in sorted(zip(X_train_final.columns, model.feature_importances_), key=lambda x: -x[1])[:8]:
    print(f"  {name:20s} {imp:.3f}")

#  Save the trained model + the fitted encoder (needed to transform new data identically at prediction time)
joblib.dump(model, BASE_DIR / "injury_risk_model.pkl")
joblib.dump(ohe, BASE_DIR / "session_type_encoder.pkl")
print("\nSaved injury_risk_model.pkl and session_type_encoder.pkl")
