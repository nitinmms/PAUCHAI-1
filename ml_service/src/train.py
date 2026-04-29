"""
Train pouch cost prediction model.

Usage:
    python src/train.py                          # Random Forest (default)
    python src/train.py --model xgb             # XGBoost
    python src/train.py --model both            # compare RF vs XGBoost, save the winner
    python src/train.py --data path/to/file.xlsx
"""

import argparse
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

NUMERIC_FEATURES     = ["width", "height", "gusset", "thickness", "quantity"]
CATEGORICAL_FEATURES = ["material_type", "printing_type", "pouch_type", "zip_lock"]
ALL_FEATURES         = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET               = "actual_cost_per_pouch"

MODELS_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODELS_DIR / "pouch_cost_model.joblib"


# ── Preprocessor ──────────────────────────────────────────────────────────────

def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("num", numeric, NUMERIC_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])


def build_rf() -> Pipeline:
    return Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", RandomForestRegressor(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=42,
        )),
    ])


def build_xgb() -> Pipeline:
    return Pipeline([
        ("preprocessor", build_preprocessor()),
        ("model", XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            n_jobs=-1,
            random_state=42,
            verbosity=0,
        )),
    ])


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate_holdout(name: str, pipeline: Pipeline,
                     X_train, X_test, y_train, y_test) -> dict:
    pipeline.fit(X_train, y_train)
    y_pred  = pipeline.predict(X_test)
    mae     = mean_absolute_error(y_test, y_pred)
    rmse    = mean_squared_error(y_test, y_pred) ** 0.5
    r2      = r2_score(y_test, y_pred)

    print(f"\n  [{name}] Hold-out test metrics:")
    print(f"    MAE  : Rs.{mae:.4f}")
    print(f"    RMSE : Rs.{rmse:.4f}")
    print(f"    R2   : {r2:.4f}")
    return {"name": name, "mae": mae, "rmse": rmse, "r2": r2, "pipeline": pipeline}


def cross_validate(name: str, pipeline: Pipeline, X, y, folds: int = 5) -> float:
    cv = KFold(n_splits=folds, shuffle=True, random_state=42)
    neg_rmse = cross_val_score(
        pipeline, X, y,
        cv=cv,
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
    )
    rmse_scores = -neg_rmse
    print(f"\n  [{name}] {folds}-fold CV RMSE: "
          f"Rs.{rmse_scores.mean():.4f} +/- Rs.{rmse_scores.std():.4f}")
    return float(rmse_scores.mean())


# ── Feature importance ────────────────────────────────────────────────────────

def print_feature_importance(pipeline: Pipeline) -> None:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        return

    preprocessor = pipeline.named_steps["preprocessor"]
    cat_encoder   = preprocessor.named_transformers_["cat"].named_steps["encoder"]
    cat_names     = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    feature_names = NUMERIC_FEATURES + cat_names

    importances = model.feature_importances_
    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)

    print("\n  Top feature importances:")
    for feat, imp in pairs[:10]:
        bar = "#" * int(imp * 50)
        print(f"    {feat:<35} {imp:.4f}  {bar}")


# ── Main ──────────────────────────────────────────────────────────────────────

def train(data_path: Path, model_choice: str) -> None:
    print(f"Loading data from {data_path} ...")
    df = pd.read_excel(data_path)
    print(f"  {len(df)} rows, {df.shape[1]} columns")

    df = df.dropna(subset=[TARGET])
    X = df[ALL_FEATURES]
    y = df[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"  Train: {len(X_train)}  Test: {len(X_test)}")

    candidates = []

    if model_choice in ("rf", "both"):
        print("\nTraining Random Forest ...")
        rf_pipeline = build_rf()
        cross_validate("RF", build_rf(), X_train, y_train)
        result = evaluate_holdout("Random Forest", rf_pipeline, X_train, X_test, y_train, y_test)
        candidates.append(result)

    if model_choice in ("xgb", "both"):
        print("\nTraining XGBoost ...")
        xgb_pipeline = build_xgb()
        cross_validate("XGBoost", build_xgb(), X_train, y_train)
        result = evaluate_holdout("XGBoost", xgb_pipeline, X_train, X_test, y_train, y_test)
        candidates.append(result)

    # Pick winner by lowest RMSE
    best = min(candidates, key=lambda r: r["rmse"])

    if len(candidates) > 1:
        print(f"\n  Winner: {best['name']} (RMSE Rs.{best['rmse']:.4f})")

    print_feature_importance(best["pipeline"])

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best["pipeline"], MODEL_PATH)
    print(f"\nModel saved -> {MODEL_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path,
        default=Path(__file__).parent.parent / "data" / "pouches_sample.xlsx",
    )
    parser.add_argument(
        "--model", choices=["rf", "xgb", "both"], default="rf",
        help="Which model to train. 'both' trains both and saves the winner.",
    )
    args = parser.parse_args()
    train(args.data, args.model)
