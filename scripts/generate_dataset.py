"""
SkyGuard AI - Dataset Generator
Generates realistic baseline weather time-series data for Automatic Weather Stations.
Produces:
- Diurnal solar cycles for Temperature and Humidity (inverse relationship)
- Semi-diurnal barometric pressure wave
- Realistic Gaussian sensor noise and seasonal variations
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_station_data(
    station_id: str,
    name: str,
    base_temp: float = 28.0,
    base_pressure: float = 1008.0,
    base_humidity: float = 65.0,
    temp_amplitude: float = 7.0,
    days: int = 30,
    interval_minutes: int = 10,
    start_date: str = "2026-08-01 00:00:00"
) -> pd.DataFrame:
    start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    total_steps = int((days * 24 * 60) / interval_minutes)
    timestamps = [start + timedelta(minutes=i * interval_minutes) for i in range(total_steps)]

    hours = np.array([ts.hour + ts.minute / 60.0 for ts in timestamps])
    day_indices = np.array([i / (24 * 60 / interval_minutes) for i in range(total_steps)])

    # Diurnal solar temperature curve (peaks ~14:30)
    temp_solar = temp_amplitude * np.sin((hours - 8.5) * np.pi / 12.0)
    # Day-to-day synoptic weather wave
    temp_synoptic = 2.0 * np.sin(day_indices * 2 * np.pi / 5.0)
    temp_noise = np.random.normal(0, 0.35, total_steps)
    temperature = np.round(base_temp + temp_solar + temp_synoptic + temp_noise, 2)

    # Semi-diurnal barometric pressure oscillation (peaks ~09:00 and ~21:00)
    pres_solar = 1.8 * np.sin((hours - 3.0) * 2 * np.pi / 24.0)
    pres_synoptic = 3.5 * np.cos(day_indices * 2 * np.pi / 6.0)
    pres_noise = np.random.normal(0, 0.25, total_steps)
    pressure = np.round(base_pressure + pres_solar + pres_synoptic + pres_noise, 2)

    # Relative humidity (inversely correlated with temperature diurnal curve)
    hum_solar = - (temp_amplitude * 1.8) * np.sin((hours - 8.5) * np.pi / 12.0)
    hum_synoptic = - 1.5 * temp_synoptic
    hum_noise = np.random.normal(0, 1.2, total_steps)
    humidity = np.clip(np.round(base_humidity + hum_solar + hum_synoptic + hum_noise, 1), 5.0, 100.0)

    df = pd.DataFrame({
        "station_id": station_id,
        "station_name": name,
        "timestamp": [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps],
        "temperature": temperature,
        "pressure": pressure,
        "humidity": humidity,
        "label": "normal",
        "fault_type": "none"
    })
    return df

def generate_all_stations():
    stations = [
        {"id": "AWS-001", "name": "Delhi Safdarjung", "temp": 31.0, "pres": 1005.0, "hum": 62.0, "amp": 8.0},
        {"id": "AWS-002", "name": "Mumbai Colaba", "temp": 29.5, "pres": 1009.0, "hum": 82.0, "amp": 4.5},
        {"id": "AWS-003", "name": "Chennai Nungambakkam", "temp": 30.0, "pres": 1008.0, "hum": 76.0, "amp": 5.0},
        {"id": "AWS-004", "name": "Kolkata Alipore", "temp": 29.8, "pres": 1007.5, "hum": 79.0, "amp": 6.0},
        {"id": "AWS-005", "name": "Bengaluru HAL", "temp": 24.5, "pres": 915.0, "hum": 58.0, "amp": 9.0},
        {"id": "AWS-006", "name": "Hyderabad Begumpet", "temp": 27.8, "pres": 952.0, "hum": 55.0, "amp": 8.5},
    ]

    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/generated", exist_ok=True)

    dfs = []
    for s in stations:
        df = generate_station_data(
            s["id"], s["name"],
            base_temp=s["temp"],
            base_pressure=s["pres"],
            base_humidity=s["hum"],
            temp_amplitude=s["amp"],
            days=15
        )
        csv_path = f"data/raw/{s['id']}_raw.csv"
        df.to_csv(csv_path, index=False)
        print(f"Generated {len(df)} readings for {s['id']} -> {csv_path}")
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    combined.to_csv("data/generated/all_stations_normal.csv", index=False)
    print(f"Combined normal dataset saved: {len(combined)} records.")

if __name__ == "__main__":
    generate_all_stations()
