"""
SkyGuard AI - Dynamic Evaluation Regression Test Suite
Verifies that model evaluation metrics are generated dynamically from predictions and ground-truth labels
rather than static constants.
"""
import pytest
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ml.evaluator import run_evaluation, BENCHMARK_DATASET_PATH

def test_dynamic_evaluation_pipeline():
    """Verify that evaluation pipeline executes, measures latency, and produces numeric metrics."""
    result = run_evaluation()
    
    assert result["status"] == "completed", f"Evaluation failed: {result.get('error_message')}"
    assert result["evaluated_samples"] > 0, "Evaluated samples must be non-zero"
    assert result["avg_detection_latency_ms"] > 0.0, "Detection latency must be measured (> 0 ms)"
    
    metrics = result.get("metrics")
    assert metrics is not None, "Metrics object must exist"
    
    for metric_key in ["precision", "recall", "f1_score", "false_positive_rate"]:
        assert metric_key in metrics, f"Metric {metric_key} missing"
        val = metrics[metric_key]
        assert isinstance(val, (int, float)), f"{metric_key} must be numeric"
        assert 0.0 <= val <= 100.0, f"{metric_key} value {val} out of range [0.0, 100.0]"

    assert "fault_type_breakdown" in result, "Fault type breakdown missing"
    assert len(result["fault_type_breakdown"]) > 0, "Fault breakdown must contain evaluated categories"

def test_evaluation_metrics_are_dynamic():
    """
    Regression test proving metrics are dynamically computed from ground truth.
    Creates a temporary modified subset of observations and verifies that calculated metrics change.
    """
    temp_dataset_path = "data/processed/temp_test_eval_dataset.csv"
    
    # Create sample synthetic evaluation dataset
    df_eval = pd.DataFrame({
        "station_id": ["AWS-001"] * 50,
        "station_name": ["Test Station"] * 50,
        "timestamp": pd.date_range("2026-01-01", periods=50, freq="10min").astype(str),
        "temperature": [25.0] * 40 + [55.0] * 10, # 10 spike anomalies
        "pressure": [1013.25] * 50,
        "humidity": [60.0] * 50,
        "label": ["NORMAL"] * 40 + ["SPIKE"] * 10,
        "fault_type": ["none"] * 40 + ["temperature_spike"] * 10,
        "ground_truth_is_anomaly": [0] * 40 + [1] * 10,
        "ground_truth_sensor": ["none"] * 40 + ["temperature"] * 10,
        "is_missing": [False] * 50
    })
    
    df_eval.to_csv(temp_dataset_path, index=False)
    
    try:
        res1 = run_evaluation(temp_dataset_path)
        assert res1["status"] == "completed"
        prec1 = res1["metrics"]["precision"]
        samples1 = res1["evaluated_samples"]
        assert samples1 == 50
        
        # Modify dataset: flip ground truth labels to test dynamic metric change
        df_eval_mod = df_eval.copy()
        df_eval_mod["ground_truth_is_anomaly"] = [1] * 50 # all anomalous now
        df_eval_mod.to_csv(temp_dataset_path, index=False)
        
        res2 = run_evaluation(temp_dataset_path)
        assert res2["status"] == "completed"
        prec2 = res2["metrics"]["precision"]
        
        # Metrics must differ when ground-truth labels change!
        assert prec1 != prec2, "Evaluation metrics must be dynamic and change when ground truth changes!"
    finally:
        if os.path.exists(temp_dataset_path):
            os.remove(temp_dataset_path)

if __name__ == "__main__":
    print("Running evaluation pipeline tests directly...")
    test_dynamic_evaluation_pipeline()
    test_evaluation_metrics_are_dynamic()
    print("Dynamic evaluation regression tests passed successfully!")
