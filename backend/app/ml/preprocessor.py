"""
SkyGuard AI - Data Preprocessor
Handles data validation, feature engineering, and temporal feature creation for AWS sensor data.
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

SENSOR_RANGES = {
    "temperature": (-50.0, 60.0),   # Celsius
    "pressure": (850.0, 1085.0),    # hPa
    "humidity": (0.0, 100.0),       # %
}

def validate_sensor_values(df: pd.DataFrame) -> pd.DataFrame:
    """Flag out-of-range sensor values as suspect."""
    df = df.copy()
    if 'data_quality' not in df.columns:
        df['data_quality'] = 'OK'
    for sensor, (lo, hi) in SENSOR_RANGES.items():
        if sensor in df.columns:
            mask = df[sensor].notna() & ((df[sensor] < lo) | (df[sensor] > hi))
            if mask.any():
                df.loc[mask, 'data_quality'] = 'SUSPECT'
    return df

def compute_temporal_features(
    df: pd.DataFrame,
    window_short: int = 6,
    window_long: int = 24
) -> pd.DataFrame:
    """
    Compute rolling statistics, rate of change, persistence, and cross-sensor relations.
    Expects df sorted by timestamp for a single station.
    """
    df = df.copy()
    sensors = ['temperature', 'pressure', 'humidity']

    for sensor in sensors:
        if sensor not in df.columns:
            continue

        col = pd.to_numeric(df[sensor], errors='coerce').astype(float).interpolate(limit=3)

        # Rolling mean & std
        df[f'{sensor}_roll_mean_short'] = col.rolling(window_short, min_periods=2).mean()
        df[f'{sensor}_roll_std_short'] = col.rolling(window_short, min_periods=2).std()
        df[f'{sensor}_roll_mean_long'] = col.rolling(window_long, min_periods=4).mean()
        df[f'{sensor}_roll_std_long'] = col.rolling(window_long, min_periods=4).std()

        # Rate of change
        df[f'{sensor}_roc'] = col.diff().fillna(0)
        df[f'{sensor}_roc3'] = col.diff(3).fillna(0)

        # Deviation from short-term baseline
        std_short = df[f'{sensor}_roll_std_short'].replace(0, np.nan)
        df[f'{sensor}_deviation'] = ((col - df[f'{sensor}_roll_mean_short']) / std_short).fillna(0)

        # Persistence: std over window
        df[f'{sensor}_persistence'] = col.rolling(window_short, min_periods=2).std().fillna(0)

    # Cross-parameter features
    if all(s in df.columns for s in ['temperature', 'pressure', 'humidity']):
        temp_s = pd.to_numeric(df['temperature'], errors='coerce')
        pres_s = pd.to_numeric(df['pressure'], errors='coerce')
        hum_s = pd.to_numeric(df['humidity'], errors='coerce')
        df['temp_pressure_diff'] = (
            temp_s.diff().fillna(0).abs() -
            pres_s.diff().fillna(0).abs() / 5.0
        )
        df['temp_humidity_ratio'] = np.where(
            hum_s > 0,
            temp_s / (hum_s + 0.1),
            0.0
        )

    return df

def prepare_features_for_model(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """
    Extract numeric features for Isolation Forest.
    """
    feature_cols = [
        'temperature', 'pressure', 'humidity',
        'temperature_deviation', 'pressure_deviation', 'humidity_deviation',
        'temperature_roc', 'pressure_roc', 'humidity_roc',
        'temperature_persistence', 'pressure_persistence', 'humidity_persistence',
        'temp_pressure_diff'
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].copy()
    X = X.ffill().bfill().fillna(0)
    return X.values, available

def preprocess_station_data(records: List[Dict[str, Any]], station_id: str) -> pd.DataFrame:
    """Full preprocessing pipeline for incoming station records."""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        df = df.sort_values('timestamp').drop_duplicates(subset='timestamp').reset_index(drop=True)
    
    sensors = [s for s in ['temperature', 'pressure', 'humidity'] if s in df.columns]
    if sensors:
        df['is_missing'] = df[sensors].isna().all(axis=1)
    else:
        df['is_missing'] = False

    df = validate_sensor_values(df)
    df = compute_temporal_features(df)
    return df
