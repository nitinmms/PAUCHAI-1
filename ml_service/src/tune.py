"""
Hyperparameter search for the pouch cost model.

Usage:
    python src/tune.py                    # tune both RF and XGBoost
    python src/tune.py --model rf
    python src/tune.py --model xgb
    python src/tune.py --data path/to/file.xlsx --iter 50
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
from sklearn.model_selection import KFold, RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

NUMERIC_FEATURES     = ["width", "height", "gusset", "thickness", "quantity"]
CATEGORICAL_FEATURES = ["material_type", "printing_type", "pouch_type", "zip_lock"]
ALL_FEATURES         = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET               = "actual_cost_per_pouch"

MODELS_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODELS_DIR / "pouch_cost_model.joblib"


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


RF_PARAM_DIST = {
    "model__n_estimators":   [100, 200, 300, 500],
    "model__max_depth":      [None, 10, 20, 30],
    "model__min_samples_leaf": [1, 2, 4, 8],
    "model__max_features":   ["sqrt", "log2", 0.5, 0.8],
}

XGB_PARAM_DIST = {
    "model__n_estimators":    [200, 400, 600, 800],
    "model__learning_rate":   [0.01, 0.03, 0.05, 0.1, 0.15],
    "model__max_depth":       [4, 5, 6, 7, 8],
    "model__subsample":       [0.6, 0.7, 0.8, 0.9, 1.0],
    "model__colsample_bytree":[0.6, 0.7, 0.8, 0.9, 1.0],
    "model__reg_alpha":       [0, 0.01, 0.05, 0.1, 0.5],
    "model__reg_lambda":      [0.5, 1.0, 2.0, 5.0],
}


def make_pipeline(model_name: str) -> Pipeline:
    model = (
        RandomForestRegressor(n_jobs=-1, random_state=42)
        if model_name == "rf"
        else XGBRegressor(n_jobs=-1, random_state=42, verbosity=0)
    )
    return Pipeline([("preprocessor", build_preprocessor()), ("model", model)])


def tune_model(name: str, X_train, y_train, param_dist: dict, n_iter: int) -> tuple[Pipeline, dict]:
    print(f"\n  Tuning {name} ({n_iter} random candidates, 5-fold CV) ...")

    search = RandomizedSearchCV(
        estimator=make_pipeline(name),
        param_distributions=param_dist,
        n_iter=n_iter,
        scoring="neg_root_mean_squared_error",
        cv=KFold(n_splits=5, shuffle=True, random_state=42),
        n_jobs=-1,
        random_state=42,
        verbose=1,
        refit=True,
    )
    search.fit(X_train, y_train)

    best_rmse = -search.best_score_
    print(f"  Best CV RMSE: Rs.{best_rmse:.4f}")
    print(f"  Best params: {search.best_params_}")
    return search.best_estimator_, search.best_params_


def evaluate(name: str, pipeline: Pipeline, X_test, y_test) -> float:
    y_pred = pipeline.predict(X_test)
    mae    = mean_absolute_error(y_test, y_pred)
    rmse   = mean_squared_error(y_test, y_pred) ** 0.5
    r2     = r2_score(y_test, y_pred)
    print(f"\n  [{name}] Hold-out test metrics after tuning:")
    print(f"    MAE  : Rs.{mae:.4f}")
    print(f"    RMSE : Rs.{rmse:.4f}")
    print(f"    R2   : {r2:.4f}")
    return rmse


def tune(data_path: Path, model_choice: str, n_iter: int) -> None:
    print(f"Loading data from {data_path} ...")
    df = pd.read_excel(data_path)
    df = df.dropna(subset=[TARGET])
    X = df[ALL_FEATURES]
    y = df[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"  Train: {len(X_train)}  Test: {len(X_test)}")

    winners = []

    if model_choice in ("rf", "both"):
        pipeline, _ = tune_model("rf", X_train, y_train, RF_PARAM_DIST, n_iter)
        rmse = evaluate("Random Forest (tuned)", pipeline, X_test, y_test)
        winners.append(("Random Forest", rmse, pipeline))

    if model_choice in ("xgb", "both"):
        pipeline, _ = tune_model("xgb", X_train, y_train, XGB_PARAM_DIST, n_iter)
        rmse = evaluate("XGBoost (tuned)", pipeline, X_test, y_test)
        winners.append(("XGBoost", rmse, pipeline))

    best_name, best_rmse, best_pipeline = min(winners, key=lambda x: x[1])
    if len(winners) > 1:
        print(f"\n  Winner after tuning: {best_name} (RMSE Rs.{best_rmse:.4f})")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)
    print(f"\nTuned model saved -> {MODEL_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path,
        default=Path(__file__).parent.parent / "data" / "pouches_sample.xlsx",
    )
    parser.add_argument(
        "--model", choices=["rf", "xgb", "both"], default="both",
    )
    parser.add_argument(
        "--iter", type=int, default=30,
        help="Number of random parameter candidates to try per model.",
    )
    args = parser.parse_args()
    tune(args.data, args.model, args.iter)
