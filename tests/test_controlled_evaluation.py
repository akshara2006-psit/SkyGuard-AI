"""
SkyGuard AI - Phase 5C Controlled Evaluation Focused Tests
Tests:
- Deterministic anomaly injection & reproducibility
- Ground-truth labels & structure
- Presence of all required anomaly categories (A through H)
- Genuine weather event ground-truth isolation
- Pipeline execution & metric calculations
- Zero production database modification
"""

import sys
import os
import sqlite3
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.ml.controlled_evaluation import (
    ControlledAnomalyInjector,
    ControlledEvaluator,
    EVALUATION_DIR,
    EVAL_DATASET_PATH,
    EVAL_PREDICTIONS_PATH,
    EVAL_METRICS_PATH,
    EVAL_REPORT_PATH
)


class TestControlledAnomalyInjection:
    """Verifies deterministic anomaly injection and ground-truth structure."""

    def test_deterministic_anomaly_injection(self):
        injector = ControlledAnomalyInjector(seed=42)
        df = injector.generate_evaluation_dataset(n_per_station=50)
        assert len(df) == 100, f"Expected 100 observations, got {len(df)}"

    def test_reproducibility_with_fixed_seed(self):
        injector1 = ControlledAnomalyInjector(seed=42)
        df1 = injector1.generate_evaluation_dataset(n_per_station=50)

        injector2 = ControlledAnomalyInjector(seed=42)
        df2 = injector2.generate_evaluation_dataset(n_per_station=50)

        pd.testing.assert_frame_equal(df1, df2)

    def test_ground_truth_labels_structure(self):
        injector = ControlledAnomalyInjector(seed=42)
        df = injector.generate_evaluation_dataset(n_per_station=500)
        
        required_cols = [
            "timestamp",
            "station_id",
            "sensor_type",
            "original_value",
            "evaluation_value",
            "ground_truth_anomaly",
            "ground_truth_type",
            "temperature",
            "pressure",
            "humidity",
            "is_missing"
        ]
        for col in required_cols:
            assert col in df.columns, f"Required column '{col}' missing from evaluation dataset"

        unique_anom = set(df["ground_truth_anomaly"].unique())
        assert unique_anom.issubset({0, 1}), f"ground_truth_anomaly must be binary 0 or 1, got {unique_anom}"

    def test_each_required_anomaly_type(self):
        injector = ControlledAnomalyInjector(seed=42)
        df = injector.generate_evaluation_dataset(n_per_station=500)
        
        required_types = {
            "temperature_spike",
            "pressure_spike",
            "humidity_spike",
            "frozen_sensor",
            "sensor_drift",
            "missing_telemetry",
            "multivariate_inconsistency",
            "genuine_weather_event",
            "normal"
        }
        present_types = set(df["ground_truth_type"].unique())
        assert required_types.issubset(present_types), (
            f"Missing required anomaly categories: {required_types - present_types}"
        )

    def test_genuine_weather_event_not_labeled_as_sensor_anomaly(self):
        injector = ControlledAnomalyInjector(seed=42)
        df = injector.generate_evaluation_dataset(n_per_station=500)
        
        weather_rows = df[df["ground_truth_type"] == "genuine_weather_event"]
        assert len(weather_rows) > 0, "No genuine weather event samples generated"
        assert (weather_rows["ground_truth_anomaly"] == 0).all(), (
            "Genuine weather events must NOT be labeled as sensor anomalies (ground_truth_anomaly must be 0)"
        )


class TestControlledPipelineExecutionAndMetrics:
    """Verifies pipeline execution and mathematical consistency of metrics."""

    def test_pipeline_execution_and_metric_calculations(self):
        injector = ControlledAnomalyInjector(seed=42)
        # Use smaller sample for quick test execution
        df = injector.generate_evaluation_dataset(n_per_station=80)
        
        evaluator = ControlledEvaluator()
        results = evaluator.evaluate(df, save_outputs=False)

        assert results["status"] == "completed"
        assert "primary_metrics" in results
        
        pm = results["primary_metrics"]
        required_metrics = [
            "true_positives",
            "false_positives",
            "true_negatives",
            "false_negatives",
            "precision_pct",
            "recall_pct",
            "f1_score_pct",
            "false_positive_rate_pct",
            "false_negative_rate_pct",
            "detection_rate_pct"
        ]
        for m in required_metrics:
            assert m in pm, f"Metric '{m}' missing from results"

        # Check ranges
        for pct_key in ["precision_pct", "recall_pct", "f1_score_pct", "false_positive_rate_pct", "false_negative_rate_pct", "detection_rate_pct"]:
            val = pm[pct_key]
            assert isinstance(val, (int, float))
            assert 0.0 <= val <= 100.0, f"Metric {pct_key} = {val} out of valid [0, 100] range"

        # Check genuine weather evaluation section
        assert "genuine_weather_event_evaluation" in results
        gw = results["genuine_weather_event_evaluation"]
        assert "correct_genuine_event_classifications" in gw
        assert "false_alarm_rate_pct" in gw

    def test_evaluation_artifacts_saved_separately(self):
        assert os.path.exists(EVAL_DATASET_PATH), "evaluation_dataset.csv not found"
        assert os.path.exists(EVAL_PREDICTIONS_PATH), "evaluation_predictions.csv not found"
        assert os.path.exists(EVAL_METRICS_PATH), "evaluation_metrics.json not found"
        assert os.path.exists(EVAL_REPORT_PATH), "evaluation_report.md not found"

    def test_no_production_database_modification(self):
        db_path = "backend/database/skyguard.db"
        assert os.path.exists(db_path), "Production database not found"
        
        def get_db_counts():
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            demo_cnt = c.execute("SELECT COUNT(*) FROM sensor_readings WHERE station_id LIKE 'AWS-%'").fetchone()[0]
            noaa_ids = ['KATL','KBOS','KDEN','KDFW','KJFK','KLAX','KORD','KSFO']
            ph = ','.join(['?' for _ in noaa_ids])
            noaa_cnt = c.execute(f"SELECT COUNT(*) FROM sensor_readings WHERE station_id IN ({ph})", noaa_ids).fetchone()[0]
            tot_cnt = c.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0]
            anom_cnt = c.execute("SELECT COUNT(*) FROM anomalies").fetchone()[0]
            conn.close()
            return demo_cnt, noaa_cnt, tot_cnt, anom_cnt

        before = get_db_counts()
        
        # Run evaluation
        injector = ControlledAnomalyInjector(seed=42)
        df = injector.generate_evaluation_dataset(n_per_station=40)
        evaluator = ControlledEvaluator()
        evaluator.evaluate(df, save_outputs=False)

        after = get_db_counts()

        assert before == after, f"Production database was modified! Before: {before}, After: {after}"
        assert after[0] == 26680, f"Demo readings changed: {after[0]} != 26680"
        assert after[1] == 13756, f"NOAA readings changed: {after[1]} != 13756"
        assert after[2] == 40436, f"Total readings changed: {after[2]} != 40436"
