"""
SkyGuard AI - Controlled Anomaly-Injection Evaluation Engine
Phase 5C: Evaluates existing production detection pipeline against controlled, reproducible ground-truth.

Key Design Principles:
1. Strict database safety: Never modifies, inserts, or deletes production SQLite tables.
2. Controlled injection: Injects deterministic, physics-based anomalies (Spikes, Frozen, Drift, Telemetry, Multivariate, Genuine Weather).
3. Reuses existing production pipeline: Isolation Forest, TemporalAnalyzer, SeasonalBaselineLearner, MultivariateAnalyzer, SpatialAnalyzer, CauseClassifier, ValueCorrector.
4. Transparent metrics: Computes real TP, FP, TN, FN, Precision, Recall, F1, FPR, FNR, Detection Rate without inventing or inflating performance.
5. Independent evaluation storage: Outputs saved exclusively to backend/data/evaluation/.
"""

import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

from .analyzer import SkyGuardAnalyzer

logger = logging.getLogger(__name__)

EVALUATION_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evaluation")
EVAL_DATASET_PATH = os.path.join(EVALUATION_DIR, "evaluation_dataset.csv")
EVAL_PREDICTIONS_PATH = os.path.join(EVALUATION_DIR, "evaluation_predictions.csv")
EVAL_METRICS_PATH = os.path.join(EVALUATION_DIR, "evaluation_metrics.json")
EVAL_REPORT_PATH = os.path.join(EVALUATION_DIR, "evaluation_report.md")


class ControlledAnomalyInjector:
    """
    Injects reproducible, parameterized synthetic sensor anomalies and genuine weather events
    into a representative baseline dataset of valid sensor observations.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    def generate_evaluation_dataset(
        self,
        base_df: Optional[pd.DataFrame] = None,
        n_per_station: int = 500
    ) -> pd.DataFrame:
        """
        Constructs an evaluation dataset with known ground-truth labels across 8 required categories:
        A. Temperature spike
        B. Pressure spike
        C. Humidity spike
        D. Frozen sensor
        E. Sensor drift
        F. Missing telemetry
        G. Multivariate inconsistency
        H. Genuine weather-like event (coherent multi-sensor shift)
        """
        np.random.seed(self.seed)

        if base_df is None:
            raw_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "generated", "all_stations_normal.csv")
            if not os.path.exists(raw_path):
                raw_path = "data/generated/all_stations_normal.csv"
            
            raw_df = pd.read_csv(raw_path)
            s1 = raw_df[raw_df["station_id"] == "AWS-001"].head(n_per_station).copy().reset_index(drop=True)
            s2 = raw_df[raw_df["station_id"] == "AWS-002"].head(n_per_station).copy().reset_index(drop=True)
            df = pd.concat([s1, s2], ignore_index=True)
        else:
            df = base_df.copy().reset_index(drop=True)

        df["sensor_type"] = "none"
        df["original_value"] = None
        df["evaluation_value"] = None
        df["ground_truth_anomaly"] = 0
        df["ground_truth_type"] = "normal"
        df["is_missing"] = False

        def inject_spike(idx: int, sensor: str, delta: float, ftype: str):
            orig = float(df.loc[idx, sensor])
            new_val = orig + delta
            if sensor == "humidity":
                new_val = np.clip(new_val, 0.0, 100.0)
            df.loc[idx, "original_value"] = orig
            df.loc[idx, sensor] = round(new_val, 2)
            df.loc[idx, "evaluation_value"] = round(new_val, 2)
            df.loc[idx, "sensor_type"] = sensor
            df.loc[idx, "ground_truth_anomaly"] = 1
            df.loc[idx, "ground_truth_type"] = ftype

        def inject_frozen(start_idx: int, length: int, sensor: str):
            frozen_val = float(df.loc[start_idx - 1, sensor])
            for i in range(start_idx, start_idx + length):
                orig = float(df.loc[i, sensor])
                df.loc[i, "original_value"] = orig
                df.loc[i, sensor] = frozen_val
                df.loc[i, "evaluation_value"] = frozen_val
                df.loc[i, "sensor_type"] = sensor
                df.loc[i, "ground_truth_anomaly"] = 1
                df.loc[i, "ground_truth_type"] = "frozen_sensor"

        def inject_drift(start_idx: int, length: int, sensor: str, rate: float):
            for step, i in enumerate(range(start_idx, start_idx + length)):
                orig = float(df.loc[i, sensor])
                new_val = orig + (step * rate)
                if sensor == "humidity":
                    new_val = np.clip(new_val, 0.0, 100.0)
                df.loc[i, "original_value"] = orig
                df.loc[i, sensor] = round(new_val, 2)
                df.loc[i, "evaluation_value"] = round(new_val, 2)
                df.loc[i, "sensor_type"] = sensor
                df.loc[i, "ground_truth_anomaly"] = 1
                df.loc[i, "ground_truth_type"] = "sensor_drift"

        def inject_missing(start_idx: int, length: int):
            for i in range(start_idx, start_idx + length):
                df.loc[i, "original_value"] = float(df.loc[i, "temperature"])
                df.loc[i, "temperature"] = None
                df.loc[i, "pressure"] = None
                df.loc[i, "humidity"] = None
                df.loc[i, "is_missing"] = True
                df.loc[i, "sensor_type"] = "all"
                df.loc[i, "ground_truth_anomaly"] = 1
                df.loc[i, "ground_truth_type"] = "missing_telemetry"

        def inject_multivariate_inconsistency(start_idx: int, length: int, sensor: str, surge_val: float):
            for step, i in enumerate(range(start_idx, start_idx + length)):
                orig = float(df.loc[i, sensor])
                new_val = orig + surge_val
                if sensor == "humidity":
                    new_val = np.clip(new_val, 0.0, 100.0)
                df.loc[i, "original_value"] = orig
                df.loc[i, sensor] = round(new_val, 2)
                df.loc[i, "evaluation_value"] = round(new_val, 2)
                df.loc[i, "sensor_type"] = sensor
                df.loc[i, "ground_truth_anomaly"] = 1
                df.loc[i, "ground_truth_type"] = "multivariate_inconsistency"

        def inject_genuine_weather(start_idx: int, length: int):
            for step, i in enumerate(range(start_idx, start_idx + length), 1):
                t_orig = float(df.loc[i, "temperature"])
                p_orig = float(df.loc[i, "pressure"])
                h_orig = float(df.loc[i, "humidity"])
                df.loc[i, "original_value"] = t_orig
                df.loc[i, "temperature"] = round(t_orig - (step * 0.65), 2)
                df.loc[i, "pressure"] = round(p_orig - (step * 1.10), 2)
                df.loc[i, "humidity"] = round(np.clip(h_orig + (step * 2.8), 0.0, 100.0), 2)
                df.loc[i, "evaluation_value"] = df.loc[i, "temperature"]
                df.loc[i, "sensor_type"] = "multivariate_coherent"
                df.loc[i, "ground_truth_anomaly"] = 0  # CRITICAL: Genuine weather is NOT a sensor fault!
                df.loc[i, "ground_truth_type"] = "genuine_weather_event"

        # Determine station slice boundaries
        station_ids = list(df["station_id"].unique())
        n_total = len(df)
        
        if len(station_ids) >= 2:
            s1_mask = df["station_id"] == station_ids[0]
            n1 = int(s1_mask.sum())
            n2 = n_total - n1
        else:
            n1 = n_total
            n2 = 0

        scale1 = n1 / 500.0
        scale2 = n2 / 500.0 if n2 > 0 else 0.0

        def safe_spike(idx: int, sensor: str, delta: float, ftype: str):
            if 0 <= idx < n_total:
                inject_spike(idx, sensor, delta, ftype)

        def safe_frozen(start_idx: int, length: int, sensor: str):
            eff_len = min(length, max(4, int(length * (n_total / 1000.0)))) if n_total < 1000 else length
            if 1 <= start_idx and start_idx + eff_len <= n_total:
                inject_frozen(start_idx, eff_len, sensor)

        def safe_drift(start_idx: int, length: int, sensor: str, rate: float):
            eff_len = min(length, max(4, int(length * (n_total / 1000.0)))) if n_total < 1000 else length
            if 0 <= start_idx and start_idx + eff_len <= n_total:
                inject_drift(start_idx, eff_len, sensor, rate)

        def safe_missing(start_idx: int, length: int):
            eff_len = min(length, max(2, int(length * (n_total / 1000.0)))) if n_total < 1000 else length
            if 0 <= start_idx and start_idx + eff_len <= n_total:
                inject_missing(start_idx, eff_len)

        def safe_mv(start_idx: int, length: int, sensor: str, surge_val: float):
            eff_len = min(length, max(2, int(length * (n_total / 1000.0)))) if n_total < 1000 else length
            if 0 <= start_idx and start_idx + eff_len <= n_total:
                inject_multivariate_inconsistency(start_idx, eff_len, sensor, surge_val)

        def safe_weather(start_idx: int, length: int):
            eff_len = min(length, max(4, int(length * (n_total / 1000.0)))) if n_total < 1000 else length
            if 0 <= start_idx and start_idx + eff_len <= n_total:
                inject_genuine_weather(start_idx, eff_len)

        # --- STATION 1 INJECTIONS ---
        safe_spike(int(60 * scale1), "temperature", 24.5, "temperature_spike")
        safe_spike(int(90 * scale1), "pressure", 36.0, "pressure_spike")
        safe_spike(int(120 * scale1), "humidity", 42.0, "humidity_spike")
        safe_frozen(int(150 * scale1), 16, "temperature")
        safe_drift(int(190 * scale1), 18, "temperature", 0.48)
        safe_missing(int(230 * scale1), 6)
        safe_mv(int(260 * scale1), 8, "humidity", -38.0)
        safe_weather(int(290 * scale1), 11)
        safe_spike(int(330 * scale1), "temperature", -22.0, "temperature_spike")
        safe_spike(int(360 * scale1), "pressure", -32.0, "pressure_spike")
        safe_spike(int(390 * scale1), "humidity", -42.0, "humidity_spike")
        safe_frozen(int(420 * scale1), 16, "humidity")
        safe_drift(int(455 * scale1), 18, "pressure", 0.42)

        # --- STATION 2 INJECTIONS ---
        if n2 > 0:
            offset = n1
            safe_spike(offset + int(60 * scale2), "temperature", 22.0, "temperature_spike")
            safe_spike(offset + int(85 * scale2), "pressure", 34.0, "pressure_spike")
            safe_spike(offset + int(110 * scale2), "humidity", 38.0, "humidity_spike")
            safe_frozen(offset + int(135 * scale2), 16, "pressure")
            safe_drift(offset + int(175 * scale2), 18, "humidity", 0.46)
            safe_missing(offset + int(215 * scale2), 6)
            safe_mv(offset + int(245 * scale2), 8, "temperature", 18.0)
            safe_weather(offset + int(275 * scale2), 11)
            safe_spike(offset + int(315 * scale2), "temperature", -19.5, "temperature_spike")
            safe_spike(offset + int(340 * scale2), "pressure", -29.0, "pressure_spike")
            safe_spike(offset + int(365 * scale2), "humidity", -36.0, "humidity_spike")
            safe_frozen(offset + int(395 * scale2), 16, "temperature")
            safe_drift(offset + int(435 * scale2), 18, "temperature", 0.44)
            safe_missing(offset + int(470 * scale2), 6)

        return df


class ControlledEvaluator:
    """
    Executes the existing SkyGuard AI production detection pipeline against the controlled evaluation dataset
    and produces rigorous evaluation metrics.
    """

    def __init__(self, model_path: str = "./database/isolation_forest.pkl"):
        self.analyzer = SkyGuardAnalyzer(model_path)

    def evaluate(
        self,
        eval_df: pd.DataFrame,
        save_outputs: bool = True
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        pred_anomalies = []
        pred_sensor_faults = []
        pred_classes = []
        pred_fault_types = []
        anomaly_scores = []
        confidences = []
        affected_sensors = []
        corr_temps = []
        corr_press = []
        corr_hums = []

        for station_id, group in eval_df.groupby("station_id", sort=False):
            st_records = group.to_dict(orient="records")
            for i in range(len(st_records)):
                recent = st_records[max(0, i-30):i]
                latest = st_records[i]
                res = self.analyzer.analyze_reading(recent, str(station_id), latest)

                cls = res["classification"]
                is_sensor_fault = 1 if cls in [
                    "PROBABLE_SENSOR_ANOMALY",
                    "POSSIBLE_COMMUNICATION_FAILURE",
                    "POSSIBLE_DATA_QUALITY_ISSUE"
                ] else 0
                is_anom = 1 if res["is_anomaly"] else 0

                pred_anomalies.append(is_anom)
                pred_sensor_faults.append(is_sensor_fault)
                pred_classes.append(cls)
                pred_fault_types.append(res.get("fault_type") or "none")
                anomaly_scores.append(res.get("anomaly_score", 0.0))
                confidences.append(res.get("confidence", 0.0))
                affected_sensors.append(res.get("affected_sensor") or "none")
                corr_temps.append(res.get("corrected_temperature"))
                corr_press.append(res.get("corrected_pressure"))
                corr_hums.append(res.get("corrected_humidity"))

        total_duration = time.perf_counter() - start_time
        n_samples = len(eval_df)
        throughput = (n_samples / total_duration) if total_duration > 0 else 0.0
        avg_latency_ms = (total_duration / n_samples * 1000.0) if n_samples > 0 else 0.0

        predictions_df = eval_df.copy()
        predictions_df["predicted_anomaly"] = pred_anomalies
        predictions_df["predicted_sensor_fault"] = pred_sensor_faults
        predictions_df["predicted_classification"] = pred_classes
        predictions_df["predicted_fault_type"] = pred_fault_types
        predictions_df["anomaly_score"] = anomaly_scores
        predictions_df["confidence"] = confidences
        predictions_df["affected_sensor"] = affected_sensors
        predictions_df["corrected_temperature"] = corr_temps
        predictions_df["corrected_pressure"] = corr_press
        predictions_df["corrected_humidity"] = corr_hums
        predictions_df["is_correct_sensor_fault"] = (
            predictions_df["ground_truth_anomaly"] == predictions_df["predicted_sensor_fault"]
        )

        # 1. Primary Metrics: Sensor Fault Detection
        y_true = predictions_df["ground_truth_anomaly"].values
        y_pred = predictions_df["predicted_sensor_fault"].values

        tp = int(np.sum((y_true == 1) & (y_pred == 1)))
        fp = int(np.sum((y_true == 0) & (y_pred == 1)))
        tn = int(np.sum((y_true == 0) & (y_pred == 0)))
        fn = int(np.sum((y_true == 1) & (y_pred == 0)))

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
        det_rate = rec

        # 2. Anomaly Type Breakdown
        type_breakdown = {}
        for ftype, sub in predictions_df.groupby("ground_truth_type"):
            tot = len(sub)
            det = int(sub["predicted_sensor_fault"].sum())
            missed = tot - det
            det_pct = round((det / tot) * 100, 1) if tot > 0 else 0.0
            cls_counts = {k: int(v) for k, v in sub["predicted_classification"].value_counts().items()}
            
            type_breakdown[ftype] = {
                "total_injected": tot,
                "detected": det,
                "missed": missed,
                "detection_rate_pct": det_pct,
                "predicted_classifications": cls_counts
            }

        # 3. Sensor Type Breakdown
        sensor_breakdown = {}
        for stype, sub in predictions_df[predictions_df["ground_truth_anomaly"] == 1].groupby("sensor_type"):
            tot = len(sub)
            det = int(sub["predicted_sensor_fault"].sum())
            rate = round((det / tot) * 100, 1) if tot > 0 else 0.0
            sensor_breakdown[stype] = {
                "total_injected": tot,
                "detected": det,
                "detection_rate_pct": rate
            }

        # 4. Genuine Weather Event Specific Evaluation
        w_sub = predictions_df[predictions_df["ground_truth_type"] == "genuine_weather_event"]
        w_tot = len(w_sub)
        w_correct_genuine = int((w_sub["predicted_classification"] == "POSSIBLE_GENUINE_WEATHER_EVENT").sum())
        w_misclassified_fault = int((w_sub["predicted_sensor_fault"] == 1).sum())
        w_normal = int((w_sub["predicted_classification"] == "NORMAL").sum())
        w_fa_rate = round((w_misclassified_fault / w_tot * 100), 2) if w_tot > 0 else 0.0
        w_correct_rate = round((w_correct_genuine / w_tot * 100), 2) if w_tot > 0 else 0.0

        genuine_weather_metrics = {
            "total_genuine_weather_samples": w_tot,
            "correct_genuine_event_classifications": w_correct_genuine,
            "correct_genuine_event_pct": w_correct_rate,
            "incorrect_sensor_anomaly_classifications": w_misclassified_fault,
            "false_alarm_rate_pct": w_fa_rate,
            "classified_as_normal": w_normal
        }

        # 5. Results Structure
        results = {
            "evaluation_title": "SkyGuard AI - Controlled Anomaly-Injection Evaluation",
            "evaluation_type": "Controlled anomaly-injection evaluation",
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "dataset_info": {
                "total_observations": n_samples,
                "stations_evaluated": list(eval_df["station_id"].unique()),
                "anomaly_records_count": int(np.sum(y_true == 1)),
                "normal_records_count": int(np.sum((eval_df["ground_truth_type"] == "normal"))),
                "genuine_weather_records_count": w_tot,
            },
            "runtime_performance": {
                "total_evaluation_time_sec": round(total_duration, 2),
                "avg_detection_latency_ms": round(avg_latency_ms, 3),
                "throughput_obs_per_sec": round(throughput, 1)
            },
            "primary_metrics": {
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
                "precision_pct": round(prec * 100, 2),
                "recall_pct": round(rec * 100, 2),
                "f1_score_pct": round(f1 * 100, 2),
                "false_positive_rate_pct": round(fpr * 100, 2),
                "false_negative_rate_pct": round(fnr * 100, 2),
                "detection_rate_pct": round(det_rate * 100, 2)
            },
            "anomaly_type_breakdown": type_breakdown,
            "sensor_type_breakdown": sensor_breakdown,
            "genuine_weather_event_evaluation": genuine_weather_metrics,
            "limitations_notice": (
                "These metrics reflect controlled anomaly-injection evaluation across synthetic/injected scenarios "
                "on valid baseline data, NOT unbounded real-world accuracy."
            )
        }

        # 6. Save Outputs to backend/data/evaluation/
        if save_outputs:
            os.makedirs(EVALUATION_DIR, exist_ok=True)
            eval_df.to_csv(EVAL_DATASET_PATH, index=False)
            predictions_df.to_csv(EVAL_PREDICTIONS_PATH, index=False)
            with open(EVAL_METRICS_PATH, "w") as f:
                json.dump(results, f, indent=2)
            self._generate_markdown_report(results, EVAL_REPORT_PATH)

        return results

    def _generate_markdown_report(self, results: Dict[str, Any], path: str):
        pm = results["primary_metrics"]
        rp = results["runtime_performance"]
        ds = results["dataset_info"]
        gw = results["genuine_weather_event_evaluation"]

        report_content = f"""# SkyGuard AI — Controlled Anomaly-Injection Evaluation Report
**Evaluation Date**: {results['timestamp']}  
**Evaluation Type**: Controlled anomaly-injection evaluation  
**Pipeline**: SkyGuard AI Master Pipeline (Isolation Forest, TemporalAnalyzer, SeasonalBaseline, Multivariate, Spatial, CauseClassifier, ValueCorrector)  

> [!NOTE]
> **Methodological Scope**: These metrics reflect controlled anomaly injection against known ground-truth labels on a representative sample of AWS telemetry. They do NOT represent claimed unbounded real-world field accuracy.

---

## 1. Executive Summary

- **Total Observations Evaluated**: {ds['total_observations']}
- **Stations Evaluated**: {', '.join(ds['stations_evaluated'])}
- **Sensor Anomaly Injected Samples**: {ds['anomaly_records_count']}
- **Genuine Weather Injected Samples**: {ds['genuine_weather_records_count']}
- **Clean Normal Samples**: {ds['normal_records_count']}
- **Total Runtime**: {rp['total_evaluation_time_sec']} seconds ({rp['throughput_obs_per_sec']} observations/sec)
- **Average Ingestion Latency**: {rp['avg_detection_latency_ms']} ms/observation

---

## 2. Overall Sensor Fault Detection Performance

| Metric | Measured Value | Definition |
|---|---|---|
| **True Positives (TP)** | **{pm['true_positives']}** | Injected sensor faults correctly flagged |
| **False Positives (FP)** | **{pm['false_positives']}** | Non-fault observations diagnosed as sensor faults |
| **True Negatives (TN)** | **{pm['true_negatives']}** | Non-fault observations correctly diagnosed (Normal or Weather) |
| **False Negatives (FN)** | **{pm['false_negatives']}** | Injected sensor faults missed by the pipeline |
| **Precision** | **{pm['precision_pct']}%** | TP / (TP + FP) |
| **Recall (Detection Rate)** | **{pm['recall_pct']}%** | TP / (TP + FN) |
| **F1-Score** | **{pm['f1_score_pct']}%** | Harmonic mean of Precision & Recall |
| **False Positive Rate (FPR)** | **{pm['false_positive_rate_pct']}%** | FP / (FP + TN) |
| **False Negative Rate (FNR)** | **{pm['false_negative_rate_pct']}%** | FN / (FN + TP) |

---

## 3. Anomaly Type Breakdown

| Anomaly Category | Injected Samples | Detected | Missed | Detection Rate | Primary Diagnostic Classifications |
|---|---|---|---|---|---|
"""
        for ftype, data in results["anomaly_type_breakdown"].items():
            classes_str = ", ".join([f"{k}: {v}" for k, v in data["predicted_classifications"].items()])
            report_content += f"| `{ftype}` | {data['total_injected']} | {data['detected']} | {data['missed']} | **{data['detection_rate_pct']}%** | {classes_str} |\n"

        report_content += f"""
---

## 4. Sensor Type Breakdown

| Sensor Type | Injected Faults | Detected | Detection Rate |
|---|---|---|---|
"""
        for stype, data in results["sensor_type_breakdown"].items():
            report_content += f"| `{stype}` | {data['total_injected']} | {data['detected']} | **{data['detection_rate_pct']}%** |\n"

        report_content += f"""
---

## 5. Genuine Weather Event Discriminative Evaluation

The objective is to verify that SkyGuard AI distinguishes coordinated atmospheric variations (fronts, storms, airmass shifts) from isolated hardware sensor malfunctions.

- **Total Injected Genuine Events**: {gw['total_genuine_weather_samples']}
- **Correctly Classified as Genuine Weather Event (`POSSIBLE_GENUINE_WEATHER_EVENT`)**: **{gw['correct_genuine_event_classifications']} ({gw['correct_genuine_event_pct']}%)**
- **Incorrectly Misclassified as Sensor Malfunction (`PROBABLE_SENSOR_ANOMALY`)**: **{gw['incorrect_sensor_anomaly_classifications']} ({gw['false_alarm_rate_pct']}%)**
- **Classified as Normal Baseline**: {gw['classified_as_normal']}

---

## 6. Runtime Performance & Computational Efficiency

- **Total Observations Processed**: {ds['total_observations']}
- **Wall-Clock Duration**: {rp['total_evaluation_time_sec']} seconds
- **Throughput**: {rp['throughput_obs_per_sec']} observations/second
- **Mean Processing Latency**: {rp['avg_detection_latency_ms']} ms/observation

---

## 7. Limitations & Honest Assessment

1. **Synthetic & Controlled Context**: Evaluated on controlled injections on representative AWS telemetry; real sensor degradation exhibits broader mechanical and environmental nuances.
2. **Drift & Multi-Sensor Interaction**: Sensor drift on one parameter during natural diurnal shifts in companion channels is occasionally classified as a meteorological event if background diurnal drift is non-negligible.
3. **Database Integrity**: The evaluation executed entirely in-memory and through isolated files. Zero production SQLite tables were modified.
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(report_content)


def run_controlled_evaluation(seed: int = 42) -> Dict[str, Any]:
    injector = ControlledAnomalyInjector(seed=seed)
    eval_df = injector.generate_evaluation_dataset()
    evaluator = ControlledEvaluator()
    return evaluator.evaluate(eval_df, save_outputs=True)
