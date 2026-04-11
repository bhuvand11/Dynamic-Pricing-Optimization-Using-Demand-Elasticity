"""
Model Training Utilities for Dynamic Pricing Project (Phase 3)
"""

import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from feature_engineering import split_scale_for_modeling


def load_phase3_data(filepath="../data/walmart_ml_ready.csv"):
    """Load the Phase 2 output dataset."""
    return pd.read_csv(filepath)


def train_three_models(X_train, y_train, random_state=42):
    """Train baseline and tree-based models."""
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=300,
            max_depth=18,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            random_state=random_state,
        ),
    }

    trained = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        trained[name] = model

    return trained


def evaluate_models(models, X_test, y_test):
    """Evaluate models on holdout set."""
    rows = []
    predictions = {}

    for name, model in models.items():
        y_pred = model.predict(X_test)
        predictions[name] = y_pred

        mae = mean_absolute_error(y_test, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        r2 = r2_score(y_test, y_pred)

        rows.append(
            {
                "Model": name,
                "MAE": mae,
                "RMSE": rmse,
                "R2": r2,
            }
        )

    metrics_df = pd.DataFrame(rows).sort_values(by="RMSE", ascending=True).reset_index(drop=True)
    return metrics_df, predictions


def get_best_model_name(metrics_df):
    """Choose best model by RMSE then MAE."""
    ordered = metrics_df.sort_values(["RMSE", "MAE"], ascending=[True, True])
    return ordered.iloc[0]["Model"]


def save_phase3_artifacts(
    metrics_df,
    models,
    best_model_name,
    scaler,
    feature_columns,
    out_models_dir="../models",
    out_output_dir="../output",
):
    """Persist metrics, best model, and metadata."""
    os.makedirs(out_models_dir, exist_ok=True)
    os.makedirs(out_output_dir, exist_ok=True)

    metrics_path = os.path.join(out_output_dir, "phase3_model_metrics.csv")
    metrics_df.to_csv(metrics_path, index=False)

    best_model = models[best_model_name]
    best_model_path = os.path.join(out_models_dir, "best_demand_model.joblib")
    joblib.dump(best_model, best_model_path)

    scaler_path = os.path.join(out_models_dir, "phase3_scaler.joblib")
    joblib.dump(scaler, scaler_path)

    meta = {
        "best_model": best_model_name,
        "feature_columns": feature_columns,
        "metric_primary": "RMSE",
    }
    metadata_path = os.path.join(out_models_dir, "phase3_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "metrics_csv": metrics_path,
        "best_model_file": best_model_path,
        "scaler_file": scaler_path,
        "metadata_file": metadata_path,
    }


def run_phase3_pipeline(
    input_path="../data/walmart_ml_ready.csv",
    test_size=0.2,
    random_state=42,
):
    """Complete Phase 3 training pipeline."""
    df = load_phase3_data(input_path)

    X_train, X_test, y_train, y_test, scaler, scaled_cols = split_scale_for_modeling(
        df,
        target_col="Weekly_Sales",
        date_col="Date",
        test_size=test_size,
    )

    models = train_three_models(X_train, y_train, random_state=random_state)
    metrics_df, predictions = evaluate_models(models, X_test, y_test)
    best_model_name = get_best_model_name(metrics_df)

    artifacts = save_phase3_artifacts(
        metrics_df,
        models,
        best_model_name,
        scaler,
        feature_columns=list(X_train.columns),
    )

    return {
        "train_shape": X_train.shape,
        "test_shape": X_test.shape,
        "metrics": metrics_df,
        "best_model": best_model_name,
        "predictions": predictions,
        "y_test": y_test,
        "artifacts": artifacts,
        "scaled_columns": scaled_cols,
    }


if __name__ == "__main__":
    result = run_phase3_pipeline()
    print("Phase 3 training complete")
    print(f"Train shape: {result['train_shape']}")
    print(f"Test shape: {result['test_shape']}")
    print("\nModel Metrics:")
    print(result["metrics"])
    print(f"\nBest model: {result['best_model']}")
    print("\nSaved artifacts:")
    for k, v in result["artifacts"].items():
        print(f"- {k}: {v}")
