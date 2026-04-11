"""
Data Processing Utilities for Dynamic Pricing Project
"""

import pandas as pd
import numpy as np
from datetime import datetime


def load_data(filepath='../data/Walmart.csv'):
    """
    Load the Walmart sales dataset.
    
    Parameters:
    -----------
    filepath : str
        Path to the CSV file
        
    Returns:
    --------
    pd.DataFrame
        Loaded dataset
    """
    df = pd.read_csv(filepath)
    print(f"Dataset loaded successfully!")
    print(f"Shape: {df.shape}")
    return df


def convert_date_features(df, date_column='Date'):
    """
    Convert date column to datetime and extract temporal features.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    date_column : str
        Name of the date column
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with temporal features
    """
    df = df.copy()
    
    # Convert to datetime
    df[date_column] = pd.to_datetime(df[date_column], format='%d-%m-%Y')
    
    # Extract features
    df['Year'] = df[date_column].dt.year
    df['Month'] = df[date_column].dt.month
    df['Week'] = df[date_column].dt.isocalendar().week
    df['Day_of_Week'] = df[date_column].dt.dayofweek
    df['Quarter'] = df[date_column].dt.quarter
    
    return df


def create_season_feature(df, month_column='Month'):
    """
    Create season feature from month.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    month_column : str
        Name of month column
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with season feature
    """
    def get_season(month):
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
    
    df = df.copy()
    df['Season'] = df[month_column].apply(get_season)
    return df


def create_lag_features(df, target_column='Weekly_Sales', group_column='Store', lags=[1, 2]):
    """
    Create lag features for time series data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    target_column : str
        Column to create lags for
    group_column : str
        Column to group by (e.g., Store)
    lags : list
        List of lag periods
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with lag features
    """
    df = df.copy()
    
    for lag in lags:
        df[f'{target_column}_Lag_{lag}'] = df.groupby(group_column)[target_column].shift(lag)
    
    return df


def create_rolling_features(df, target_column='Weekly_Sales', group_column='Store', windows=[4, 8]):
    """
    Create rolling statistics features.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    target_column : str
        Column to calculate rolling stats for
    group_column : str
        Column to group by
    windows : list
        List of window sizes
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with rolling features
    """
    df = df.copy()
    
    for window in windows:
        # Shift by one to ensure each row only uses past information.
        df[f'{target_column}_Rolling_Mean_{window}'] = df.groupby(group_column)[target_column].transform(
            lambda x: x.shift(1).rolling(window=window, min_periods=1).mean()
        )
        df[f'{target_column}_Rolling_Std_{window}'] = df.groupby(group_column)[target_column].transform(
            lambda x: x.shift(1).rolling(window=window, min_periods=1).std()
        )
    
    return df


def simulate_price_feature(df, base_price_range=(80, 120), random_seed=42):
    """
    Simulate realistic price feature for pricing analysis.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe (must have 'Store' and 'Season' columns)
    base_price_range : tuple
        Range for base prices
    random_seed : int
        Random seed for reproducibility
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with simulated price feature
    """
    df = df.copy()
    np.random.seed(random_seed)
    
    # Base price per store from store id only (no target-derived signal).
    store_min = df['Store'].min()
    store_max = df['Store'].max()
    if store_max == store_min:
        store_rank = np.ones(len(df)) * 0.5
    else:
        store_rank = (df['Store'] - store_min) / (store_max - store_min)

    df['Base_Price'] = (base_price_range[0] + (store_rank * 20)).astype(float)
    
    # Seasonal price adjustments
    season_price_factor = {
        'Winter': 1.05,
        'Spring': 1.0,
        'Summer': 0.95,
        'Fall': 1.02
    }
    
    if 'Season' in df.columns:
        df['Season_Price_Factor'] = df['Season'].map(season_price_factor)
    else:
        df['Season_Price_Factor'] = 1.0
    
    # Add modest macro adjustment independent of target.
    fuel_norm = (df['Fuel_Price'] - df['Fuel_Price'].mean()) / (df['Fuel_Price'].std() + 1e-8)
    cpi_norm = (df['CPI'] - df['CPI'].mean()) / (df['CPI'].std() + 1e-8)
    econ_factor = 1 + (0.02 * fuel_norm) + (0.01 * cpi_norm)

    # Final price with random variation
    df['Price'] = (
        df['Base_Price'] * 
        df['Season_Price_Factor'] * 
        econ_factor *
        (1 + np.random.normal(0, 0.05, len(df)))
    ).round(2)
    
    # Ensure positive prices
    df['Price'] = df['Price'].clip(lower=base_price_range[0] * 0.8)
    
    return df


def check_missing_values(df):
    """
    Check for missing values in dataframe.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
        
    Returns:
    --------
    pd.DataFrame
        Summary of missing values
    """
    missing = pd.DataFrame({
        'Missing_Count': df.isnull().sum(),
        'Missing_Percentage': (df.isnull().sum() / len(df)) * 100
    })
    missing = missing[missing['Missing_Count'] > 0].sort_values('Missing_Count', ascending=False)
    
    if len(missing) == 0:
        print("✓ No missing values found!")
        return None
    else:
        print(f"⚠ Missing values found in {len(missing)} columns")
        return missing


def detect_outliers_iqr(df, column):
    """
    Detect outliers using IQR method.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    column : str
        Column to check for outliers
        
    Returns:
    --------
    tuple
        (outliers_df, lower_bound, upper_bound)
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    
    return outliers, lower_bound, upper_bound


def preprocess_full_pipeline(filepath='../data/Walmart.csv'):
    """
    Execute complete preprocessing pipeline.
    
    Parameters:
    -----------
    filepath : str
        Path to raw data file
        
    Returns:
    --------
    pd.DataFrame
        Fully preprocessed dataframe
    """
    print("=" * 60)
    print("STARTING DATA PREPROCESSING PIPELINE")
    print("=" * 60)
    
    # Load data
    print("\n[1/7] Loading data...")
    df = load_data(filepath)
    
    # Convert dates
    print("[2/7] Converting date features...")
    df = convert_date_features(df)
    
    # Create season
    print("[3/7] Creating season feature...")
    df = create_season_feature(df)
    
    # Sort data
    print("[4/7] Sorting data...")
    df = df.sort_values(['Store', 'Date']).reset_index(drop=True)
    
    # Create lag features
    print("[5/7] Creating lag features...")
    df = create_lag_features(df)
    
    # Create rolling features
    print("[6/7] Creating rolling features...")
    df = create_rolling_features(df)
    
    # Simulate price
    print("[7/7] Simulating price feature...")
    df = simulate_price_feature(df)
    
    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE!")
    print("=" * 60)
    print(f"Final shape: {df.shape}")
    print(f"Features created: {len(df.columns)}")
    
    return df


if __name__ == "__main__":
    # Example usage
    print("Data Processing Module for Dynamic Pricing Project")
    print("-" * 60)
    
    # Run full pipeline
    df_processed = preprocess_full_pipeline()
    
    # Save processed data
    output_path = '../data/walmart_processed.csv'
    df_processed.to_csv(output_path, index=False)
    print(f"\n✓ Processed data saved to: {output_path}")
    
    # Display sample
    print("\n" + "=" * 60)
    print("SAMPLE OF PROCESSED DATA")
    print("=" * 60)
    print(df_processed.head())
