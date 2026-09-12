"""
SkyGuard AI - Focused Seasonal & Temporal Baseline Learning Tests
Tests:
1. Normal temporal / diurnal behavior (tracking baseline envelopes)
2. Seasonal deviation (isolated out-of-season reading detected with clear explanation)
3. Insufficient history handling (graceful fallback without false alarms)
4. Legitimate weather variation / front passage (distinguished from sensor hardware fault)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ml.seasonal_baseline import SeasonalBaselineLearner, get_season_name
from app.ml.cause_classifier import CauseClassifier, POSSIBLE_GENUINE_WEATHER_EVENT, PROBABLE_SENSOR_ANOMALY, NORMAL
from app.ml.analyzer import SkyGuardAnalyzer

def generate_synthetic_history(days=7, base_temp=25.0, diurnal_amp=6.0, base_pres=1012.0, base_hum=60.0):
    start = datetime(2026, 1, 1, 0, 0, 0)
    timestamps = [start + timedelta(minutes=15 * i) for i in range(days * 96)]
    records = []
    for ts in timestamps:
        # Diurnal temperature cycle: peaks around 14:00, coldest around 05:00
        hour_rad = (ts.hour - 14) * 2 * np.pi / 24
        t = base_temp + diurnal_amp * np.cos(hour_rad) + np.random.normal(0, 0.4)
        # Inverse humidity cycle
        h = base_hum - (diurnal_amp * 2.0) * np.cos(hour_rad) + np.random.normal(0, 1.0)
        # Semidiurnal atmospheric pressure tide (~1.5 hPa wave)
        p = base_pres + 1.2 * np.cos(ts.hour * 4 * np.pi / 24) + np.random.normal(0, 0.2)
        records.append({
            "timestamp": ts.isoformat(),
            "temperature": round(float(t), 2),
            "pressure": round(float(p), 2),
            "humidity": round(float(np.clip(h, 10, 95)), 2)
        })
    return pd.DataFrame(records)

def test_normal_temporal_behavior():
    """Verify that observations tracking the learned diurnal profile remain within baseline bounds."""
    df_hist = generate_synthetic_history(days=5, base_temp=22.0, diurnal_amp=5.0)
    learner = SeasonalBaselineLearner(min_history_samples=24)
    
    # Normal test reading at 14:00 (expected peak: ~27°C)
    current_reading = {
        "timestamp": "2026-01-06T14:00:00",
        "temperature": 26.8,
        "pressure": 1012.2,
        "humidity": 51.0
    }
    
    result = learner.fit_and_evaluate(df_hist, current_reading)
    assert result.has_sufficient_history is True
    assert result.seasonal_anomaly_detected is False
    assert "temperature" in result.findings
    assert result.findings["temperature"].is_seasonal_outlier is False
    assert result.findings["temperature"].z_score < 2.0
    print("Normal temporal behavior test passed.")

def test_seasonal_deviation_detection():
    """Verify that an isolated, unseasonal temperature reading triggers an explainable seasonal outlier flag."""
    df_hist = generate_synthetic_history(days=7, base_temp=10.0, diurnal_amp=4.0) # Cold winter baseline (6-14°C)
    learner = SeasonalBaselineLearner(min_history_samples=24, outlier_z_threshold=3.29)
    
    # Abnormal reading: 38°C in winter at midnight
    outlier_reading = {
        "timestamp": "2026-01-08T02:00:00",
        "temperature": 38.5,
        "pressure": 1012.0,
        "humidity": 65.0
    }
    
    result = learner.fit_and_evaluate(df_hist, outlier_reading)
    assert result.has_sufficient_history is True
    assert result.seasonal_anomaly_detected is True
    assert result.findings["temperature"].is_seasonal_outlier is True
    assert result.findings["temperature"].z_score > 3.29
    assert "deviates significantly" in result.findings["temperature"].description
    print("Seasonal deviation detection test passed.")

def test_insufficient_history_handling():
    """Verify that learner gracefully handles sparse history without raising false alarms or crashing."""
    df_short = pd.DataFrame([
        {"timestamp": "2026-01-01T00:00:00", "temperature": 20.0, "pressure": 1013.0, "humidity": 50.0},
        {"timestamp": "2026-01-01T01:00:00", "temperature": 19.5, "pressure": 1013.1, "humidity": 52.0}
    ])
    learner = SeasonalBaselineLearner(min_history_samples=24)
    
    current_reading = {
        "timestamp": "2026-01-01T02:00:00",
        "temperature": 25.0,
        "pressure": 1013.0,
        "humidity": 50.0
    }
    
    result = learner.fit_and_evaluate(df_short, current_reading)
    assert result.has_sufficient_history is False
    assert result.seasonal_anomaly_detected is False
    assert "Insufficient historical data" in result.description
    print("Insufficient history test passed.")

def test_legitimate_weather_variation():
    """
    Verify that multi-sensor atmospheric shifts (e.g. cold front passage: temp drops,
    pressure climbs, humidity drops) are recognized as genuine weather events rather than sensor faults.
    """
    df_hist = generate_synthetic_history(days=7, base_temp=28.0, diurnal_amp=5.0, base_pres=1008.0, base_hum=70.0)
    learner = SeasonalBaselineLearner(min_history_samples=24, outlier_z_threshold=2.5)
    
    # Strong unseasonal cold front: sharp simultaneous changes across all three parameters
    front_reading = {
        "timestamp": "2026-01-08T14:00:00",
        "temperature": 12.0, # ~16°C below normal
        "pressure": 1024.0,   # ~16 hPa above normal
        "humidity": 30.0     # ~40% below normal
    }
    
    seasonal_res = learner.fit_and_evaluate(df_hist, front_reading)
    assert seasonal_res.has_sufficient_history is True
    assert seasonal_res.coherent_seasonal_shift is True
    
    classifier = CauseClassifier()
    # Mock multivariate coherent change
    from app.ml.multivariate_analyzer import MultivariateResult
    mv_coherent = MultivariateResult(
        coherent_change=True,
        isolated_sensor=None,
        weather_event_likelihood=0.85,
        sensor_fault_likelihood=0.10,
        description="Coordinated atmospheric variation detected."
    )
    
    classification = classifier.classify(
        anomaly_score=0.45,
        temporal_findings={},
        multivariate_result=mv_coherent,
        spatial_result=None,
        seasonal_result=seasonal_res
    )
    
    assert classification.classification == POSSIBLE_GENUINE_WEATHER_EVENT
    assert classification.classification != PROBABLE_SENSOR_ANOMALY
    assert "Genuine Meteorological Event" in classification.probable_cause
    print("Legitimate weather variation test passed.")

if __name__ == "__main__":
    test_normal_temporal_behavior()
    test_seasonal_deviation_detection()
    test_insufficient_history_handling()
    test_legitimate_weather_variation()
    print("\nALL 4 FOCUSED SEASONAL TESTS PASSED SUCCESSFULLY!")
