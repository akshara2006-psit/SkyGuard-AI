"""
SkyGuard AI - Fault Injection Pipeline
Injects realistic, controlled, reproducible synthetic anomalies into AWS data:
1. Sudden spikes (Temperature, Pressure, Humidity)
2. Frozen sensor (stuck transducer)
3. Sensor drift (gradual calibration loss)
4. Missing data (packet loss)
5. Communication/telemetry failure (prolonged gap)
6. Multivariate anomaly (isolated channel anomaly)
7. Genuine meteorological event (multi-parameter coherent change)
"""
import pandas as pd
import numpy as np
import os
import random

def inject_anomalies(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    random.seed(seed)
    df = df.copy().reset_index(drop=True)

    n = len(df)
    df["label"] = "normal"
    df["fault_type"] = "none"
    df["ground_truth_is_anomaly"] = 0
    df["ground_truth_sensor"] = "none"

    # 1. Temperature Spikes
    spike_idx = [int(n * 0.12), int(n * 0.45), int(n * 0.78)]
    for idx in spike_idx:
        df.loc[idx, "temperature"] += np.random.uniform(18.0, 35.0)
        df.loc[idx, "label"] = "spike"
        df.loc[idx, "fault_type"] = "temperature_spike"
        df.loc[idx, "ground_truth_is_anomaly"] = 1
        df.loc[idx, "ground_truth_sensor"] = "temperature"

    # 2. Pressure Spikes
    p_spike_idx = [int(n * 0.28), int(n * 0.65)]
    for idx in p_spike_idx:
        df.loc[idx, "pressure"] += np.random.uniform(25.0, 45.0)
        df.loc[idx, "label"] = "spike"
        df.loc[idx, "fault_type"] = "pressure_spike"
        df.loc[idx, "ground_truth_is_anomaly"] = 1
        df.loc[idx, "ground_truth_sensor"] = "pressure"

    # 3. Frozen Humidity Sensor
    f_start = int(n * 0.35)
    frozen_val = df.loc[f_start, "humidity"]
    for i in range(f_start, min(f_start + 10, n)):
        df.loc[i, "humidity"] = frozen_val + np.random.normal(0, 0.005)
        df.loc[i, "label"] = "frozen_sensor"
        df.loc[i, "fault_type"] = "frozen_sensor"
        df.loc[i, "ground_truth_is_anomaly"] = 1
        df.loc[i, "ground_truth_sensor"] = "humidity"

    # 4. Temperature Sensor Drift
    d_start = int(n * 0.52)
    for step_i, i in enumerate(range(d_start, min(d_start + 18, n))):
        df.loc[i, "temperature"] += (step_i * 0.65)
        df.loc[i, "label"] = "drift"
        df.loc[i, "fault_type"] = "drift"
        df.loc[i, "ground_truth_is_anomaly"] = 1
        df.loc[i, "ground_truth_sensor"] = "temperature"

    # 5. Missing Data / Telemetry Dropout
    m_start = int(n * 0.70)
    for i in range(m_start, min(m_start + 6, n)):
        df.loc[i, "temperature"] = np.nan
        df.loc[i, "pressure"] = np.nan
        df.loc[i, "humidity"] = np.nan
        df.loc[i, "label"] = "communication_failure"
        df.loc[i, "fault_type"] = "communication_failure"
        df.loc[i, "ground_truth_is_anomaly"] = 1
        df.loc[i, "ground_truth_sensor"] = "all"

    # 6. Genuine Meteorological Event
    w_start = int(n * 0.85)
    for i in range(w_start, min(w_start + 8, n)):
        df.loc[i, "temperature"] -= np.random.uniform(4.5, 7.0)
        df.loc[i, "pressure"] -= np.random.uniform(8.0, 14.0)
        df.loc[i, "humidity"] = np.clip(df.loc[i, "humidity"] + np.random.uniform(22.0, 35.0), 10.0, 100.0)
        df.loc[i, "label"] = "possible_weather_event"
        df.loc[i, "fault_type"] = "possible_weather_event"
        df.loc[i, "ground_truth_is_anomaly"] = 1
        df.loc[i, "ground_truth_sensor"] = "meteorological"

    return df

def process_all():
    os.makedirs("data/processed", exist_ok=True)
    raw_path = "data/generated/all_stations_normal.csv"
    if not os.path.exists(raw_path):
        from generate_dataset import generate_all_stations
        generate_all_stations()

    raw_df = pd.read_csv(raw_path)
    fault_dfs = []
    for station_id, group in raw_df.groupby("station_id"):
        fault_df = inject_anomalies(group)
        fault_dfs.append(fault_df)
        out_single = f"data/processed/{station_id}_with_faults.csv"
        fault_df.to_csv(out_single, index=False)
        print(f"Fault dataset created for {station_id} -> {out_single}")

    combined = pd.concat(fault_dfs, ignore_index=True)
    out_all = "data/processed/benchmark_dataset_with_ground_truth.csv"
    combined.to_csv(out_all, index=False)
    print(f"Full benchmark dataset saved: {len(combined)} samples ({out_all})")

if __name__ == "__main__":
    process_all()
