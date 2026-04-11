"""
Phase 4: Price Elasticity and Revenue Optimization Utilities
"""

import json
import os

import joblib
import numpy as np
import pandas as pd


def load_phase4_inputs(
    data_path="../data/walmart_ml_ready.csv",
    model_path="../models/best_demand_model.joblib",
    scaler_path="../models/phase3_scaler.joblib",
    metadata_path="../models/phase3_metadata.json",
):
    """Load modeling data, trained model, scaler, and metadata."""
    df = pd.read_csv(data_path)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    feature_cols = metadata["feature_columns"]
    return df, model, scaler, metadata, feature_cols


def get_context_rows(df, context="latest_per_store"):
    """Select rows used as baseline market context for simulation."""
    data = df.copy()

    if context == "latest_per_store":
        if "Date" not in data.columns or "Store" not in data.columns:
            raise ValueError("Need Date and Store columns for latest_per_store context.")
        data = data.sort_values(["Store", "Date"]).groupby("Store", as_index=False).tail(1)
        data = data.reset_index(drop=True)
    elif context == "latest_global":
        if "Date" not in data.columns:
            raise ValueError("Need Date column for latest_global context.")
        latest_date = data["Date"].max()
        data = data[data["Date"] == latest_date].copy().reset_index(drop=True)
    else:
        raise ValueError("context must be latest_per_store or latest_global")

    return data


def _prepare_feature_matrix(df_sim, feature_cols, scaler):
    """Build scaled feature matrix matching Phase 3 model expectations."""
    X = df_sim[feature_cols].copy()
    X_scaled = X.copy()

    # Phase 3 scaler was fit on all model feature columns in this order.
    X_scaled.loc[:, feature_cols] = scaler.transform(X[feature_cols])
    return X_scaled


def simulate_price_response(
    context_df,
    model,
    scaler,
    feature_cols,
    price_multipliers=None,
):
    """
    Simulate demand and revenue across candidate price multipliers.

    Note:
        Here demand is model-predicted Weekly_Sales (project proxy).
        Revenue score follows project formula: Price * PredictedDemand.
    """
    if price_multipliers is None:
        price_multipliers = np.linspace(0.8, 1.2, 21)

    results = []

    base = context_df.copy()
    base["Base_Sim_Price"] = base["Price"]

    for mult in price_multipliers:
        df_sim = base.copy()
        df_sim["Price_Multiplier"] = float(mult)
        df_sim["Simulated_Price"] = df_sim["Base_Sim_Price"] * mult

        # Replace price feature and price-dependent interactions.
        df_sim["Price"] = df_sim["Simulated_Price"]
        if {"Price_Holiday_Interaction", "Holiday_Flag"}.issubset(df_sim.columns):
            df_sim["Price_Holiday_Interaction"] = df_sim["Price"] * df_sim["Holiday_Flag"]
        if {"Price_Unemployment_Interaction", "Unemployment"}.issubset(df_sim.columns):
            df_sim["Price_Unemployment_Interaction"] = df_sim["Price"] * df_sim["Unemployment"]

        X_scaled = _prepare_feature_matrix(df_sim, feature_cols, scaler)
        demand_pred = model.predict(X_scaled)

        df_sim["Predicted_Demand"] = demand_pred
        df_sim["Predicted_Revenue"] = df_sim["Simulated_Price"] * df_sim["Predicted_Demand"]

        keep_cols = [
            "Store",
            "Date",
            "Base_Sim_Price",
            "Price_Multiplier",
            "Simulated_Price",
            "Predicted_Demand",
            "Predicted_Revenue",
        ]
        keep_cols = [c for c in keep_cols if c in df_sim.columns]
        results.append(df_sim[keep_cols])

    sim_df = pd.concat(results, axis=0, ignore_index=True)
    return sim_df


def estimate_store_elasticity(sim_df):
    """Estimate store-level elasticity using log-log slope from simulation output."""
    rows = []

    for store_id, g in sim_df.groupby("Store"):
        g = g.copy().sort_values("Simulated_Price")
        g = g[(g["Simulated_Price"] > 0) & (g["Predicted_Demand"] > 0)]

        if len(g) < 3:
            rows.append({"Store": store_id, "Elasticity": np.nan})
            continue

        x = np.log(g["Simulated_Price"].values)
        y = np.log(g["Predicted_Demand"].values)

        slope, intercept = np.polyfit(x, y, 1)
        rows.append(
            {
                "Store": store_id,
                "Elasticity": float(slope),
                "LogLog_Intercept": float(intercept),
            }
        )

    return pd.DataFrame(rows)


def get_optimal_price_by_store(sim_df):
    """Pick price multiplier maximizing predicted revenue for each store."""
    idx = sim_df.groupby("Store")["Predicted_Revenue"].idxmax()
    best = sim_df.loc[idx].copy().sort_values("Store").reset_index(drop=True)

    best = best.rename(
        columns={
            "Simulated_Price": "Optimal_Price",
            "Predicted_Demand": "Optimal_Demand",
            "Predicted_Revenue": "Optimal_Revenue",
        }
    )

    return best


def recommend_guardrailed_prices(sim_df, elasticity_df):
    """
    Generate business-realistic price recommendations using guardrails.

    Guardrails are based on elasticity segments:
    - High sensitivity (elasticity <= -0.10): tighter increase cap, stricter demand floor
    - Medium sensitivity (-0.10 < elasticity <= -0.05): moderate cap/floor
    - Low sensitivity (elasticity > -0.05): wider cap/softer floor
    """
    sim = sim_df.copy()
    ela_map = elasticity_df.set_index("Store")["Elasticity"].to_dict()

    rec_rows = []

    for store_id, g in sim.groupby("Store"):
        g = g.copy().sort_values("Price_Multiplier")

        # Baseline context around current price (multiplier 1.0).
        base_idx = (g["Price_Multiplier"] - 1.0).abs().idxmin()
        base_row = g.loc[base_idx]

        elasticity = float(ela_map.get(store_id, np.nan))

        if np.isnan(elasticity):
            segment = "Unknown"
            max_mult = 1.05
            min_mult = 0.95
            demand_floor = 0.97
        elif elasticity <= -0.10:
            segment = "HighSensitivity"
            max_mult = 1.05
            min_mult = 0.90
            demand_floor = 0.97
        elif elasticity <= -0.05:
            segment = "MediumSensitivity"
            max_mult = 1.10
            min_mult = 0.90
            demand_floor = 0.95
        else:
            segment = "LowSensitivity"
            max_mult = 1.15
            min_mult = 0.90
            demand_floor = 0.93

        candidates = g[(g["Price_Multiplier"] >= min_mult) & (g["Price_Multiplier"] <= max_mult)].copy()
        candidates = candidates[candidates["Predicted_Demand"] >= (base_row["Predicted_Demand"] * demand_floor)]

        # Fall back to baseline if no candidate passes guardrails.
        if len(candidates) == 0:
            best_row = base_row
            decision = "BaselineFallback"
        else:
            best_row = candidates.loc[candidates["Predicted_Revenue"].idxmax()]
            decision = "GuardrailedOptimum"

        rec_rows.append(
            {
                "Store": int(store_id),
                "Date": best_row.get("Date", pd.NaT),
                "Elasticity": elasticity,
                "Elasticity_Segment": segment,
                "Base_Price": float(base_row["Simulated_Price"]),
                "Recommended_Price": float(best_row["Simulated_Price"]),
                "Recommended_Multiplier": float(best_row["Price_Multiplier"]),
                "Recommended_Demand": float(best_row["Predicted_Demand"]),
                "Recommended_Revenue": float(best_row["Predicted_Revenue"]),
                "Expected_Demand_Change_Pct": float((best_row["Predicted_Demand"] / base_row["Predicted_Demand"] - 1.0) * 100),
                "Expected_Revenue_Change_Pct": float((best_row["Predicted_Revenue"] / base_row["Predicted_Revenue"] - 1.0) * 100),
                "Decision_Type": decision,
            }
        )

    return pd.DataFrame(rec_rows).sort_values("Store").reset_index(drop=True)


def save_phase4_outputs(
    sim_df,
    elasticity_df,
    optimal_df,
    recommendation_df=None,
    output_dir="../output",
):
    """Save key Phase 4 tables."""
    os.makedirs(output_dir, exist_ok=True)

    sim_path = os.path.join(output_dir, "phase4_price_simulation_results.csv")
    elasticity_path = os.path.join(output_dir, "phase4_store_elasticity.csv")
    optimal_path = os.path.join(output_dir, "phase4_optimal_prices_by_store.csv")
    recommendation_path = os.path.join(output_dir, "phase4_recommended_prices_guardrailed.csv")

    sim_df.to_csv(sim_path, index=False)
    elasticity_df.to_csv(elasticity_path, index=False)
    optimal_df.to_csv(optimal_path, index=False)
    if recommendation_df is not None:
        recommendation_df.to_csv(recommendation_path, index=False)

    return {
        "simulation_csv": sim_path,
        "elasticity_csv": elasticity_path,
        "optimal_prices_csv": optimal_path,
        "recommended_prices_csv": recommendation_path,
    }


def run_phase4_pipeline(
    data_path="../data/walmart_ml_ready.csv",
    model_path="../models/best_demand_model.joblib",
    scaler_path="../models/phase3_scaler.joblib",
    metadata_path="../models/phase3_metadata.json",
    context="latest_per_store",
):
    """Complete Phase 4 pipeline."""
    df, model, scaler, metadata, feature_cols = load_phase4_inputs(
        data_path=data_path,
        model_path=model_path,
        scaler_path=scaler_path,
        metadata_path=metadata_path,
    )

    context_df = get_context_rows(df, context=context)
    sim_df = simulate_price_response(context_df, model, scaler, feature_cols)
    elasticity_df = estimate_store_elasticity(sim_df)
    optimal_df = get_optimal_price_by_store(sim_df)
    recommendation_df = recommend_guardrailed_prices(sim_df, elasticity_df)

    outputs = save_phase4_outputs(sim_df, elasticity_df, optimal_df, recommendation_df)

    return {
        "context_rows": len(context_df),
        "sim_rows": len(sim_df),
        "elasticity_summary": elasticity_df["Elasticity"].describe(),
        "optimal_summary": optimal_df[["Optimal_Price", "Optimal_Revenue"]].describe(),
        "recommended_summary": recommendation_df[["Recommended_Price", "Recommended_Revenue"]].describe(),
        "outputs": outputs,
    }


if __name__ == "__main__":
    result = run_phase4_pipeline()
    print("Phase 4 complete")
    print(f"Context rows: {result['context_rows']}")
    print(f"Simulation rows: {result['sim_rows']}")
    print("Saved files:")
    for k, v in result["outputs"].items():
        print(f"- {k}: {v}")
