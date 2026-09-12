"""
SkyGuard AI - Seasonal & Temporal Baseline Learner
Learns normal diurnal (hour-of-day) and seasonal (month/season) baseline distributions
for automated weather station observations using ONLY:
- Temperature
- Pressure
- Relative Humidity
- Timestamp

Provides explainable expected ranges, confidence intervals, and seasonal deviation metrics.
Gracefully handles insufficient historical data and explicitly avoids classifying legitimate
regional or coordinated weather changes as sensor hardware faults.
"""

import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@dataclass
class BaselineStats:
    count: int
    mean: float
    std: float
    p05: float
    p95: float

    def is_valid(self, min_samples: int = 5) -> bool:
        return self.count >= min_samples

@dataclass
class SeasonalDeviationFinding:
    sensor: str
    observed: float
    expected_mean: float
    expected_std: float
    expected_range: Tuple[float, float]
    z_score: float
    is_seasonal_outlier: bool
    context: str # e.g. "Hour 14, Winter (Jan)"
    description: str

@dataclass
class SeasonalBaselineResult:
    has_sufficient_history: bool
    total_historical_samples: int
    findings: Dict[str, SeasonalDeviationFinding] = field(default_factory=dict)
    seasonal_anomaly_detected: bool = False
    coherent_seasonal_shift: bool = False
    description: str = ""

def get_season_name(month: int) -> str:
    """Standard 4-season meteorological categorization."""
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "autumn"

class SeasonalBaselineLearner:
    """
    Lightweight, highly explainable temporal baseline learner.
    Learns:
    1. Hourly diurnal profile (0-23 hours): captures daily heating/cooling & pressure tides.
    2. Seasonal / monthly profile: captures seasonal climatic shifts.
    3. Hourly-by-season compound profile when sample depth is sufficient.
    """

    def __init__(
        self,
        min_history_samples: int = 24, # At least 24 readings (~2 hours of 5-min data or 1 day of hourly)
        min_cell_samples: int = 5,     # Minimum samples per hour/season cell
        outlier_z_threshold: float = 3.29 # 99.9% statistical interval for Gaussian
    ):
        self.min_history_samples = min_history_samples
        self.min_cell_samples = min_cell_samples
        self.outlier_z_threshold = outlier_z_threshold
        self.sensors = ["temperature", "pressure", "humidity"]

    def extract_time_features(self, dt: datetime) -> Dict[str, Any]:
        return {
            "hour": dt.hour,
            "month": dt.month,
            "season": get_season_name(dt.month)
        }

    def fit_and_evaluate(
        self,
        df_history: pd.DataFrame,
        current_record: Dict[str, Any]
    ) -> SeasonalBaselineResult:
        """
        Fits temporal baselines from historical records and evaluates current reading.
        History must contain 'timestamp' plus any of 'temperature', 'pressure', 'humidity'.
        """
        if df_history.empty or len(df_history) < self.min_history_samples:
            return SeasonalBaselineResult(
                has_sufficient_history=False,
                total_historical_samples=len(df_history),
                findings={},
                seasonal_anomaly_detected=False,
                coherent_seasonal_shift=False,
                description=(
                    f"Insufficient historical data ({len(df_history)}/{self.min_history_samples} samples) "
                    "for robust seasonal baseline profiling."
                )
            )

        df = df_history.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])

        if len(df) < self.min_history_samples:
            return SeasonalBaselineResult(
                has_sufficient_history=False,
                total_historical_samples=len(df),
                findings={},
                description="Insufficient valid timestamps for seasonal profiling."
            )

        # Parse current record timestamp
        ts_val = current_record.get("timestamp")
        if isinstance(ts_val, str):
            curr_dt = pd.to_datetime(ts_val)
        elif isinstance(ts_val, datetime):
            curr_dt = ts_val
        elif isinstance(ts_val, pd.Timestamp):
            curr_dt = ts_val.to_pydatetime()
        else:
            curr_dt = df["timestamp"].iloc[-1]

        target_hour = curr_dt.hour
        target_month = curr_dt.month
        target_season = get_season_name(target_month)

        df["hour"] = df["timestamp"].dt.hour
        df["month"] = df["timestamp"].dt.month
        df["season"] = df["month"].apply(get_season_name)

        findings: Dict[str, SeasonalDeviationFinding] = {}
        outlier_count = 0

        for sensor in self.sensors:
            if sensor not in current_record or current_record[sensor] is None:
                continue
            try:
                obs_val = float(current_record[sensor])
            except (ValueError, TypeError):
                continue

            if sensor not in df.columns:
                continue

            series = pd.to_numeric(df[sensor], errors="coerce").dropna()
            if len(series) < self.min_history_samples:
                continue

            # Hierarchical baseline matching:
            # Level 1: Same hour & same season
            # Level 2: Same hour (diurnal cycle across seasons)
            # Level 3: Overall historical station distribution
            cell_df = df[(df["hour"] == target_hour) & (df["season"] == target_season)][sensor].dropna()
            context = f"Hour {target_hour:02d}:00, {target_season.title()} (Month {target_month})"

            if len(cell_df) < self.min_cell_samples:
                cell_df = df[df["hour"] == target_hour][sensor].dropna()
                context = f"Hour {target_hour:02d}:00 (Diurnal Baseline)"

            if len(cell_df) < self.min_cell_samples:
                cell_df = series
                context = "Station Historical All-Hours Baseline"

            mean = float(cell_df.mean())
            # Floor std to prevent zero-division on highly stable signals
            std = max(float(cell_df.std()), 0.20 if sensor != "pressure" else 0.50)
            p05 = float(np.percentile(cell_df, 5)) if len(cell_df) >= 10 else mean - 2.0 * std
            p95 = float(np.percentile(cell_df, 95)) if len(cell_df) >= 10 else mean + 2.0 * std

            z = abs(obs_val - mean) / std
            is_outlier = bool(z >= self.outlier_z_threshold)

            desc = ""
            if is_outlier:
                outlier_count += 1
                desc = (
                    f"{sensor.capitalize()} {obs_val:.1f} deviates significantly ({z:.1f} sigma) "
                    f"from normal {context} baseline (expected {mean:.1f} +/- {std*2:.1f})."
                )

            findings[sensor] = SeasonalDeviationFinding(
                sensor=sensor,
                observed=round(obs_val, 2),
                expected_mean=round(mean, 2),
                expected_std=round(std, 2),
                expected_range=(round(p05, 2), round(p95, 2)),
                z_score=round(z, 2),
                is_seasonal_outlier=is_outlier,
                context=context,
                description=desc
            )

        # Multi-sensor shift analysis:
        # If multiple sensors deviate from their seasonal/diurnal normals simultaneously,
        # it strongly indicates a legitimate weather front / airmass shift rather than a sensor fault.
        coherent_shift = (outlier_count >= 2)
        anomaly_detected = (outlier_count > 0)

        if coherent_shift:
            desc = (
                f"Multi-parameter seasonal/diurnal deviation across {outlier_count} sensors "
                "consistent with synoptic weather passage or unseasonal airmass movement."
            )
        elif anomaly_detected:
            s_name = [k for k, v in findings.items() if v.is_seasonal_outlier][0]
            desc = (
                f"Isolated seasonal/diurnal deviation on {s_name} sensor relative to expected profile."
            )
        else:
            desc = "All observed parameters fall within expected diurnal and seasonal baseline envelopes."

        return SeasonalBaselineResult(
            has_sufficient_history=True,
            total_historical_samples=len(df),
            findings=findings,
            seasonal_anomaly_detected=anomaly_detected,
            coherent_seasonal_shift=coherent_shift,
            description=desc
        )
