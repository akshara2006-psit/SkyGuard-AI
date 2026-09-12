"""
SkyGuard AI - Test Suite
Tests preprocessor, temporal rules, multivariate analyzer, Isolation Forest, and cause classification.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ml.preprocessor import validate_sensor_values, compute_temporal_features, prepare_features_for_model
from app.ml.temporal_analyzer import TemporalAnalyzer
from app.ml.multivariate_analyzer import MultivariateAnalyzer
from app.ml.isolation_forest import SkyGuardIsolationForest
from app.ml.cause_classifier import CauseClassifier, PROBABLE_SENSOR_ANOMALY, POSSIBLE_GENUINE_WEATHER_EVENT, NORMAL
from app.ml.health_engine import SensorHealthEngine, compute_health_score

def test_validation_out_of_range():
    df = pd.DataFrame({"temperature": [25.0, 75.0, -90.0, 30.0], "pressure": [1013.0, 1013.0, 1013.0, 1013.0]})
    val_df = validate_sensor_values(df)
    assert val_df.loc[1, "data_quality"] == "SUSPECT"
    assert val_df.loc[2, "data_quality"] == "SUSPECT"
    assert val_df.loc[0, "data_quality"] == "OK"

def test_spike_detection():
    analyzer = TemporalAnalyzer(spike_std_threshold=3.0)
    # 10 readings at 25°C, then sudden jump to 50°C
    values = pd.Series([25.0, 25.1, 24.9, 25.0, 25.2, 25.0, 24.8, 25.1, 25.0, 50.0])
    finding = analyzer.check_spike(values, "temperature")
    assert finding.detected is True
    assert finding.fault_type == "spike"
    assert finding.severity > 0.5

def test_frozen_sensor_detection():
    analyzer = TemporalAnalyzer(frozen_tolerance=0.01, frozen_window=6)
    # Sensor stuck at exactly 25.000
    values = pd.Series([25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0])
    finding = analyzer.check_frozen(values, "humidity")
    assert finding.detected is True
    assert finding.fault_type == "frozen_sensor"

def test_sensor_drift_detection():
    analyzer = TemporalAnalyzer(drift_slope_threshold=0.2, drift_window=10)
    # Gradual steep drift: 20, 21, 22, 23, 24...
    values = pd.Series([float(x) for x in range(20, 35)])
    finding = analyzer.check_drift(values, "temperature")
    assert finding.detected is True
    assert finding.fault_type == "drift"

def test_multivariate_coherence_vs_isolation():
    mv = MultivariateAnalyzer()
    # Case A: Only temperature jumps, companion sensors are completely flat
    df_isolated = pd.DataFrame({
        "temperature": [25.0, 25.0, 25.0, 45.0, 48.0, 52.0],
        "pressure": [1010.0, 1010.0, 1010.0, 1010.1, 1010.0, 1010.1],
        "humidity": [60.0, 60.0, 60.0, 60.1, 59.9, 60.0]
    })
    res_isolated = mv.analyze(df_isolated)
    assert res_isolated.isolated_sensor == "temperature"
    assert res_isolated.sensor_fault_likelihood > res_isolated.weather_event_likelihood

    # Case B: Multi-sensor weather front
    df_front = pd.DataFrame({
        "temperature": [30.0, 29.0, 27.0, 24.0, 22.0, 20.0],
        "pressure": [1015.0, 1012.0, 1008.0, 1004.0, 1000.0, 998.0],
        "humidity": [50.0, 55.0, 65.0, 75.0, 85.0, 90.0]
    })
    res_front = mv.analyze(df_front)
    assert res_front.coherent_change is True
    assert res_front.weather_event_likelihood > res_front.sensor_fault_likelihood

def test_sensor_health_engine():
    engine = SensorHealthEngine()
    
    # 1. Healthy sensor -> high health score (>= 85%) & STABLE trend
    healthy_state = engine.update_health(
        sensor="temperature",
        recent_anomalies=[],
        total_readings=50,
        missing_readings=0,
        fault_history_count=0,
        previous_health_score=100.0
    )
    assert healthy_state.health_score >= 85.0
    assert healthy_state.status == "HEALTHY"
    assert healthy_state.degradation_trend == "STABLE"
    assert healthy_state.maintenance_status == "NOMINAL_MONITORING"
    assert 0.0 <= healthy_state.health_score <= 100.0

    # 2. Repeated anomalies -> health score decreases
    anom_state = engine.update_health(
        sensor="humidity",
        recent_anomalies=[{"is_anomaly": True}] * 8,
        total_readings=20,
        missing_readings=1,
        fault_history_count=8,
        previous_health_score=90.0
    )
    assert anom_state.health_score < 75.0
    assert anom_state.status in ["WARNING", "DEGRADED", "CRITICAL"]
    assert anom_state.degradation_trend == "DECLINING"
    assert anom_state.maintenance_status in ["INSPECTION_RECOMMENDED", "MAINTENANCE_REQUIRED", "URGENT_REPLACEMENT"]
    assert len(anom_state.maintenance_reasons) > 0

    # 3. Missing data -> reliability decreases appropriately
    missing_state = engine.update_health(
        sensor="pressure",
        recent_anomalies=[],
        total_readings=20,
        missing_readings=10, # 50% missing data
        fault_history_count=0,
        previous_health_score=95.0
    )
    assert missing_state.missing_data_rate == 0.5
    assert missing_state.health_score <= 80.0
    assert missing_state.degradation_trend == "DECLINING"

    # 4. Single isolated anomaly does NOT falsely trigger DECLINING trend if previous score was similar
    single_anom_state = engine.update_health(
        sensor="temperature",
        recent_anomalies=[{"is_anomaly": True}],
        total_readings=50,
        missing_readings=0,
        fault_history_count=1,
        previous_health_score=94.0
    )
    assert single_anom_state.health_score >= 85.0
    assert single_anom_state.degradation_trend == "STABLE"

    # 5. Deterministic reproducibility for identical input history
    res_a = engine.update_health("temperature", [{"is_anomaly": True}] * 3, 30, 2, 3, 92.0)
    res_b = engine.update_health("temperature", [{"is_anomaly": True}] * 3, 30, 2, 3, 92.0)
    assert res_a.health_score == res_b.health_score
    assert res_a.degradation_trend == res_b.degradation_trend
    assert res_a.maintenance_status == res_b.maintenance_status


def test_model_feature_attribution():
    from app.ml.feature_attribution import SkyGuardFeatureAttributor
    from app.ml.isolation_forest import SkyGuardIsolationForest

    feature_names = ["temperature", "pressure", "humidity", "temperature_deviation", "pressure_deviation", "humidity_deviation"]
    attributor = SkyGuardFeatureAttributor(feature_names)
    
    # Train dummy model
    X_train = np.random.randn(50, len(feature_names))
    model = SkyGuardIsolationForest(n_estimators=20)
    model.fit(X_train, feature_names)

    X_sample = np.array([[3.5, 0.1, 0.2, 4.2, 0.05, 0.1]]) # Temperature spike
    raw_vals = {"temperature": 55.0, "pressure": 1013.2, "humidity": 60.0, "temperature_deviation": 4.2}

    res1 = attributor.explain_sample(model.model, model.scaler, X_sample, raw_vals)
    res2 = attributor.explain_sample(model.model, model.scaler, X_sample, raw_vals)

    assert res1["model_feature_attribution_available"] is True
    assert res1["attribution_method"] == "Isolation Forest Decision Path Attribution"
    assert "feature_attributions" in res1
    assert len(res1["feature_attributions"]) == len(feature_names)
    
    # Check numeric & valid percentages
    total_pct = sum(res1["feature_attributions"].values())
    assert abs(total_pct - 1.0) < 1e-3, f"Contributions should sum to 1.0, got {total_pct}"
    
    # Check feature scope (derived ONLY from Temp, Pressure, Humidity)
    for fname in res1["feature_attributions"].keys():
        assert any(base in fname for base in ["temperature", "pressure", "humidity"]), f"Invalid feature name: {fname}"

    # Check stability (deterministic for same input)
    assert res1["feature_attributions"] == res2["feature_attributions"], "Attribution must be deterministic for identical input"
    assert len(res1["explanation_summary"]) > 0, "Explanation summary must be generated"

def test_spatial_consistency_and_scalability():
    from app.ml.spatial_analyzer import SpatialAnalyzer

    spatial = SpatialAnalyzer()
    
    target_abnormal = {"temperature": 55.0, "pressure": 1013.2, "humidity": 60.0}
    normal_peers = [
        {"temperature": 30.0, "pressure": 1013.0, "humidity": 60.0, "latitude": 28.5, "longitude": 77.2},
        {"temperature": 30.5, "pressure": 1012.8, "humidity": 61.0, "latitude": 28.6, "longitude": 77.1},
        {"temperature": 31.0, "pressure": 1013.5, "humidity": 59.0, "latitude": 28.4, "longitude": 77.3},
    ]

    # TEST 1: Target abnormal + normal peers -> NOT_SUPPORTED
    res1 = spatial.analyze(target_abnormal, normal_peers)
    assert res1.spatial_anomaly_detected is True
    assert res1.regional_pattern == "NOT_SUPPORTED"
    assert res1.neighbor_count == 3

    # TEST 2: Coherent regional weather front -> SUPPORTED
    regional_peers = [
        {"temperature": 18.0, "pressure": 995.0, "humidity": 85.0},
        {"temperature": 19.5, "pressure": 998.0, "humidity": 82.0},
        {"temperature": 27.0, "pressure": 1010.0, "humidity": 65.0},
    ]
    target_front = {"temperature": 20.0, "pressure": 996.0, "humidity": 84.0}
    res2 = spatial.analyze(target_front, regional_peers)
    assert res2.regional_pattern == "SUPPORTED"
    assert res2.spatial_anomaly_detected is False

    # TEST 3: No neighbors available -> INSUFFICIENT_EVIDENCE
    res3 = spatial.analyze(target_abnormal, [])
    assert res3.regional_pattern == "INSUFFICIENT_EVIDENCE"
    assert res3.spatial_anomaly_detected is False

    # TEST 4: Missing neighbor readings -> INSUFFICIENT_EVIDENCE (no false fault)
    missing_peers = [{"is_missing": True, "temperature": None, "pressure": None, "humidity": None}]
    res4 = spatial.analyze(target_abnormal, missing_peers)
    assert res4.regional_pattern == "INSUFFICIENT_EVIDENCE"
    assert res4.spatial_anomaly_detected is False

    # TEST 5: N-Station Scalability filtering (N=50 stations)
    synthetic_n_stations = [
        {"latitude": 28.5 + (i * 0.1), "longitude": 77.2 + (i * 0.1), "temperature": 30.0 + i}
        for i in range(50)
    ]
    filtered_neighbors = spatial.filter_neighbors_by_distance(28.5, 77.2, synthetic_n_stations, max_neighbors=5)
    assert len(filtered_neighbors) == 5, f"Should dynamically return 5 nearest neighbors, got {len(filtered_neighbors)}"

def test_simulation_scenarios_and_diagnostics():
    from app.services.simulation_service import StationSimulator, SimulationService
    from app.ml.analyzer import SkyGuardAnalyzer
    from datetime import datetime

    sim = StationSimulator("AWS-001")
    analyzer = SkyGuardAnalyzer()
    now = datetime.utcnow()

    # 1. Normal observation scope (strictly T, P, RH only)
    normal = sim.generate_normal(now)
    assert set(normal.keys()) == {"temperature", "pressure", "humidity"}
    assert -20.0 <= normal["temperature"] <= 60.0
    assert 800.0 <= normal["pressure"] <= 1100.0
    assert 0.0 <= normal["humidity"] <= 100.0

    # 2. Temperature Spike scenario
    sim.set_fault("temperature_spike", duration_steps=3)
    spike_reading = sim.generate(now)
    assert spike_reading["temperature"] > normal["temperature"] + 15.0

    # 3. Frozen sensor scenario (nearly unchanged sensor values)
    sim.set_fault("frozen_sensor", duration_steps=4)
    f1 = sim.generate(now)
    f2 = sim.generate(now)
    assert abs(f1["temperature"] - f2["temperature"]) < 0.05
    assert abs(f1["humidity"] - f2["humidity"]) < 0.05

    # 4. Drift scenario (gradual progressive deviation)
    sim.set_fault("drift", duration_steps=5)
    d1 = sim.generate(now)
    d2 = sim.generate(now)
    assert d2["temperature"] > d1["temperature"]

    # 5. Communication failure scenario (missing telemetry without inventing fake values)
    sim.set_fault("communication_failure", duration_steps=2)
    cf = sim.generate(now)
    assert cf["is_missing"] is True
    assert cf["temperature"] is None
    assert cf["pressure"] is None
    assert cf["humidity"] is None

    # 6. Genuine Weather Event scenario (coherent changes across T, P, RH)
    sim.set_fault("weather_event", duration_steps=3)
    we = sim.generate(now)
    assert we["temperature"] < normal["temperature"]
    assert we["pressure"] < normal["pressure"]
    assert we["humidity"] > normal["humidity"]

    # 7. Multivariate Inconsistency scenario
    sim.set_fault("multivariate_inconsistency", duration_steps=3)
    mi = sim.generate(now)
    assert mi["temperature"] > normal["temperature"] + 10.0
    assert mi["humidity"] > normal["humidity"] + 20.0

    # 8. Verify pipeline analysis of communication failure
    history_cf = [
        {"station_id": "AWS-004", "timestamp": (now - timedelta(minutes=10*(5-i))).isoformat(), "temperature": None, "pressure": None, "humidity": None, "is_missing": True}
        for i in range(5)
    ]
    cf_latest = {"station_id": "AWS-004", "timestamp": now.isoformat(), "temperature": None, "pressure": None, "humidity": None, "is_missing": True}
    res_cf = analyzer.analyze_reading(history_cf, "AWS-004", cf_latest)
    assert res_cf["classification"] == "POSSIBLE_COMMUNICATION_FAILURE"

    # 9. Verify pipeline analysis of coherent weather event
    history_we = [
        {"station_id": "AWS-005", "timestamp": (now - timedelta(minutes=40)).isoformat(), "temperature": 30.0, "pressure": 1012.0, "humidity": 50.0, "is_missing": False},
        {"station_id": "AWS-005", "timestamp": (now - timedelta(minutes=30)).isoformat(), "temperature": 27.0, "pressure": 1008.0, "humidity": 62.0, "is_missing": False},
        {"station_id": "AWS-005", "timestamp": (now - timedelta(minutes=20)).isoformat(), "temperature": 23.0, "pressure": 1002.0, "humidity": 78.0, "is_missing": False},
        {"station_id": "AWS-005", "timestamp": (now - timedelta(minutes=10)).isoformat(), "temperature": 20.0, "pressure": 998.0, "humidity": 88.0, "is_missing": False},
    ]
    we_latest = {"station_id": "AWS-005", "timestamp": now.isoformat(), "temperature": 18.0, "pressure": 995.0, "humidity": 92.0, "is_missing": False}
    res_we = analyzer.analyze_reading(history_we, "AWS-005", we_latest)
    assert res_we["classification"] == "POSSIBLE_GENUINE_WEATHER_EVENT"

if __name__ == "__main__":
    print("Running tests directly...")
    test_validation_out_of_range()
    test_spike_detection()
    test_frozen_sensor_detection()
    test_sensor_drift_detection()
    test_multivariate_coherence_vs_isolation()
    test_sensor_health_engine()
    test_model_feature_attribution()
    test_spatial_consistency_and_scalability()
    test_simulation_scenarios_and_diagnostics()
    print("All unit tests passed successfully!")


