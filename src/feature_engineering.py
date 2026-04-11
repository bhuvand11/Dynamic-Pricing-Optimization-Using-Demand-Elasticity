"""
Feature Engineering Utilities for Dynamic Pricing Project
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def load_processed_data(filepath="../data/walmart_model_ready.csv"):
    """
    Load processed data from Phase 1.

    Also recomputes leakage-prone derived features to keep downstream
    modeling consistent even when older intermediate files exist.
    """
    df = pd.read_csv(filepath)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    if {"Store", "Date", "Weekly_Sales"}.issubset(df.columns):
        df = df.sort_values(["Store", "Date"]).reset_index(drop=True)

        # Recompute lag and rolling features using past-only information.
        df["Sales_Lag_1"] = df.groupby("Store")["Weekly_Sales"].shift(1)
        df["Sales_Lag_2"] = df.groupby("Store")["Weekly_Sales"].shift(2)
        df["Sales_Rolling_Mean_4"] = df.groupby("Store")["Weekly_Sales"].transform(
            lambda x: x.shift(1).rolling(window=4, min_periods=1).mean()
        )
        df["Sales_Rolling_Std_4"] = df.groupby("Store")["Weekly_Sales"].transform(
            lambda x: x.shift(1).rolling(window=4, min_periods=1).std()
        )

    # Recompute simulated pricing features without target-derived leakage.
    if {"Store", "Fuel_Price", "CPI"}.issubset(df.columns):
        store_min = df["Store"].min()
        store_max = df["Store"].max()
        if store_max == store_min:
            store_rank = np.ones(len(df)) * 0.5
        else:
            store_rank = (df["Store"] - store_min) / (store_max - store_min)

        df["Base_Price"] = 80 + (store_rank * 20)

        if "Season" in df.columns:
            season_price_factor = {
                "Winter": 1.05,
                "Spring": 1.0,
                "Summer": 0.95,
                "Fall": 1.02,
            }
            df["Season_Price_Factor"] = df["Season"].map(season_price_factor)
        else:
            df["Season_Price_Factor"] = 1.0

        fuel_norm = (df["Fuel_Price"] - df["Fuel_Price"].mean()) / (df["Fuel_Price"].std() + 1e-8)
        cpi_norm = (df["CPI"] - df["CPI"].mean()) / (df["CPI"].std() + 1e-8)
        econ_factor = 1 + (0.02 * fuel_norm) + (0.01 * cpi_norm)

        np.random.seed(42)
        df["Price"] = (
            df["Base_Price"]
            * df["Season_Price_Factor"]
            * econ_factor
            * (1 + np.random.normal(0, 0.05, len(df)))
        ).round(2)
        df["Price"] = df["Price"].clip(lower=50)

    # Lag/rolling recomputation introduces initial NaNs per store.
    df = df.dropna().reset_index(drop=True)
    return df


def add_cyclical_time_features(df):
    """Encode periodic time features using sine/cosine transforms."""
    data = df.copy()

    if "Month" in data.columns:
        data["Month_sin"] = np.sin(2 * np.pi * data["Month"] / 12)
        data["Month_cos"] = np.cos(2 * np.pi * data["Month"] / 12)

    if "Week" in data.columns:
        data["Week_sin"] = np.sin(2 * np.pi * data["Week"] / 52)
        data["Week_cos"] = np.cos(2 * np.pi * data["Week"] / 52)

    if "Quarter" in data.columns:
        data["Quarter_sin"] = np.sin(2 * np.pi * data["Quarter"] / 4)
        data["Quarter_cos"] = np.cos(2 * np.pi * data["Quarter"] / 4)

    return data


def add_interaction_features(df):
    """Create interaction terms that may improve nonlinear model learning."""
    data = df.copy()

    if {"Price", "Holiday_Flag"}.issubset(data.columns):
        data["Price_Holiday_Interaction"] = data["Price"] * data["Holiday_Flag"]

    if {"Price", "Unemployment"}.issubset(data.columns):
        data["Price_Unemployment_Interaction"] = data["Price"] * data["Unemployment"]

    if {"Temperature", "Fuel_Price"}.issubset(data.columns):
        data["Temperature_Fuel_Interaction"] = data["Temperature"] * data["Fuel_Price"]

    if {"CPI", "Unemployment"}.issubset(data.columns):
        data["CPI_Unemployment_Interaction"] = data["CPI"] * data["Unemployment"]

    return data


def encode_categorical_features(df, categorical_cols=None, drop_first=False):
    """One-hot encode categorical columns."""
    data = df.copy()

    if categorical_cols is None:
        categorical_cols = [col for col in ["Season", "Holiday_Type"] if col in data.columns]

    if len(categorical_cols) == 0:
        return data

    return pd.get_dummies(data, columns=categorical_cols, drop_first=drop_first, dtype=int)


def drop_low_information_features(df, drop_cols=None, drop_constant=True):
    """
    Drop columns that add little value or cause instability in correlation/linear models.

    Defaults:
    - Day_of_Week: constant in this weekly dataset
    - Base_Price: highly redundant with Store by construction
    """
    data = df.copy()
    removed_cols = []

    if drop_cols is None:
        drop_cols = ["Day_of_Week", "Base_Price"]

    explicit_drop = [col for col in drop_cols if col in data.columns]
    if explicit_drop:
        data = data.drop(columns=explicit_drop)
        removed_cols.extend(explicit_drop)

    if drop_constant:
        constant_cols = [col for col in data.columns if data[col].nunique(dropna=False) <= 1]
        if constant_cols:
            data = data.drop(columns=constant_cols)
            removed_cols.extend(constant_cols)

    # Deduplicate while preserving order.
    removed_cols = list(dict.fromkeys(removed_cols))
    return data, removed_cols


def get_feature_target_split(df, target_col="Weekly_Sales"):
    """Split data into features X and target y."""
    data = df.copy()

    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found.")

    drop_cols = [target_col]
    # Keep Date out of training matrix to avoid type issues and leakage in random splits.
    if "Date" in data.columns:
        drop_cols.append("Date")

    X = data.drop(columns=drop_cols)
    y = data[target_col]

    return X, y


def scale_numerical_features(X, numerical_cols=None):
    """Scale numeric features using StandardScaler."""
    X_scaled = X.copy()

    if numerical_cols is None:
        numerical_cols = X_scaled.select_dtypes(include=[np.number]).columns.tolist()

    scaler = StandardScaler()
    X_scaled[numerical_cols] = scaler.fit_transform(X_scaled[numerical_cols])

    return X_scaled, scaler, numerical_cols


def split_scale_for_modeling(
    df,
    target_col="Weekly_Sales",
    date_col="Date",
    test_size=0.2,
):
    """
    Time-aware split and leakage-safe scaling for modeling.

    Returns:
        X_train_scaled, X_test_scaled, y_train, y_test, scaler, scaled_columns
    """
    data = df.copy()

    if date_col in data.columns:
        data[date_col] = pd.to_datetime(data[date_col])
        data = data.sort_values(date_col).reset_index(drop=True)

    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found.")

    split_idx = int(len(data) * (1 - test_size))
    train_df = data.iloc[:split_idx].copy()
    test_df = data.iloc[split_idx:].copy()

    drop_cols = [target_col]
    if date_col in data.columns:
        drop_cols.append(date_col)

    X_train = train_df.drop(columns=drop_cols)
    y_train = train_df[target_col]
    X_test = test_df.drop(columns=drop_cols)
    y_test = test_df[target_col]

    numerical_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    X_train_scaled[numerical_cols] = scaler.fit_transform(X_train[numerical_cols])
    X_test_scaled[numerical_cols] = scaler.transform(X_test[numerical_cols])

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, numerical_cols


def build_phase2_dataset(df):
    """Run full Phase 2 feature engineering transformations."""
    data = df.copy()

    data = add_cyclical_time_features(data)
    data = add_interaction_features(data)
    data = encode_categorical_features(data, drop_first=False)
    data, dropped_cols = drop_low_information_features(data)
    data.attrs["dropped_columns_phase2"] = dropped_cols

    return data


def run_phase2_pipeline(
    input_path="../data/walmart_model_ready.csv",
    engineered_output_path="../data/walmart_feature_engineered.csv",
    ml_ready_output_path="../data/walmart_ml_ready.csv",
):
    """Execute and save Phase 2 outputs."""
    df = load_processed_data(input_path)
    df_eng = build_phase2_dataset(df)

    # Keep exported dataset unscaled; scaling should be fit on training split in Phase 3.
    df_ml_ready = df_eng.copy()

    df_eng.to_csv(engineered_output_path, index=False)
    df_ml_ready.to_csv(ml_ready_output_path, index=False)

    return {
        "raw_shape": df.shape,
        "engineered_shape": df_eng.shape,
        "ml_ready_shape": df_ml_ready.shape,
        "dropped_columns": df_eng.attrs.get("dropped_columns_phase2", []),
        "scaled_columns": [],
    }


if __name__ == "__main__":
    summary = run_phase2_pipeline()
    print("Phase 2 feature engineering complete")
    print(f"Input shape: {summary['raw_shape']}")
    print(f"Engineered shape: {summary['engineered_shape']}")
    print(f"ML-ready shape: {summary['ml_ready_shape']}")
    print(f"Dropped columns: {summary['dropped_columns']}")
    print(f"Scaled columns: {len(summary['scaled_columns'])}")
