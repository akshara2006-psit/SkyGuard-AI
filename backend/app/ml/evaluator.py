"""
SkyGuard AI - Dynamic Model Evaluation & Benchmark Engine
Executes full ML pipeline inference across ground-truth benchmark datasets,
measures empirical inference latency, and computes real-time precision, recall, F1, FPR, and per-fault metrics.
"""
import pandas as pd
import numpy as np
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import logging

from .preprocessor import preprocess_station_data, prepare_features_for_model
from .isolation_forest import SkyGuardIsolationForest
from .temporal_analyzer import TemporalAnalyzer
from .multivariate_analyzer import MultivariateAnalyzer
from .cause_classifier import CauseClassifier

logger = logging.getLogger(__name__)

BENCHMARK_DATASET_PATH = "data/processed/benchmark_dataset_with_ground_truth.csv"
METRICS_OUTPUT_PATH = "data/processed/model_evaluation_metrics.json"

def run_evaluation(dataset_path: str = BENCHMARK_DATASET_PATH) -> Dict[str, Any]:
    """
    Executes dynamic evaluation on the specified benchmark dataset.
    Measures true inference execution latency and returns genuine evaluation metrics.
    """
    if not os.path.exists(dataset_path):
        # Fallback to check relative to root or backend
        alt_path = os.path.join("..", dataset_path)
        if os.path.exists(alt_path):
            dataset_path = alt_path
        else:
            try:
                # Attempt to generate benchmark dataset on demand
                from scripts.inject_faults import process_all
                process_all()
            except Exception as e:
                logger.error(f"Failed to generate evaluation dataset: {e}")
                return {
                    "status": "error",
                    "error_message": f"Evaluation dataset not found at {dataset_path}",
                    "evaluated_samples": 0,
                    "metrics": None
                }

    if not os.path.exists(dataset_path):
        return {
            "status": "error",
            "error_message": "Evaluation dataset unavailable or insufficient labelled data",
            "evaluated_samples": 0,
            "metrics": None
        }

    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        logger.error(f"Error reading dataset: {e}")
        return {
            "status": "error",
            "error_message": f"Failed to read evaluation dataset: {e}",
            "evaluated_samples": 0,
            "metrics": None
        }

    if df.empty or "ground_truth_is_anomaly" not in df.columns:
        return {
            "status": "error",
            "error_message": "Insufficient or invalid ground-truth labelled data",
            "evaluated_samples": 0,
            "metrics": None
        }

    y_true_all = []
    y_pred_all = []
    fault_type_all = []

    temporal = TemporalAnalyzer()
    multivariate = MultivariateAnalyzer()
    classifier = CauseClassifier()

    start_eval_time = time.perf_counter()
    total_inferences = 0

    for station_id, group in df.groupby("station_id"):
        group = group.reset_index(drop=True)
        # Preprocess station series
        processed_df = preprocess_station_data(group.to_dict(orient="records"), str(station_id))

        if processed_df.empty:
            continue

        # Train Isolation Forest on normal baseline (first 500 records)
        train_df = processed_df.iloc[:500] if len(processed_df) >= 500 else processed_df
        X_train, feature_names = prepare_features_for_model(train_df)
        model = SkyGuardIsolationForest(n_estimators=100, contamination=0.04)
        if len(X_train) > 0:
            model.fit(X_train, feature_names)

        # Score all records
        X_all, _ = prepare_features_for_model(processed_df)
        scores = model.predict_scores(X_all) if model.is_trained else np.zeros(len(processed_df))

        # Diagnostic checks per record
        for i in range(len(processed_df)):
            score = float(scores[i])
            window_slice = processed_df.iloc[max(0, i-15):i+1]
            findings = temporal.analyze(window_slice)
            mv = multivariate.analyze(window_slice)

            is_missing = bool(processed_df.loc[i, "is_missing"])
            res = classifier.classify(
                anomaly_score=score,
                temporal_findings=findings,
                multivariate_result=mv,
                missing_data=is_missing
            )

            true_label = int(group.loc[i, "ground_truth_is_anomaly"])
            pred_label = 1 if res.classification != "NORMAL" else 0

            y_true_all.append(true_label)
            y_pred_all.append(pred_label)
            fault_type_all.append(str(group.loc[i, "fault_type"]))
            total_inferences += 1

    end_eval_time = time.perf_counter()
    total_duration_sec = end_eval_time - start_eval_time
    avg_latency_ms = (total_duration_sec / total_inferences * 1000.0) if total_inferences > 0 else 0.0

    if not y_true_all:
        return {
            "status": "error",
            "error_message": "No valid observations evaluated",
            "evaluated_samples": 0,
            "metrics": None
        }

    precision = float(precision_score(y_true_all, y_pred_all, zero_division=0))
    recall = float(recall_score(y_true_all, y_pred_all, zero_division=0))
    f1 = float(f1_score(y_true_all, y_pred_all, zero_division=0))
    
    cm = confusion_matrix(y_true_all, y_pred_all)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tn, fp, fn, tp = len(y_true_all) - sum(y_pred_all), 0, 0, sum(y_pred_all)
        
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    eval_df = pd.DataFrame({
        "y_true": y_true_all,
        "y_pred": y_pred_all,
        "fault_type": fault_type_all
    })

    fault_stats = {}
    for ftype, sub in eval_df.groupby("fault_type"):
        if ftype == "none":
            continue
        tot = len(sub)
        det = int(sub["y_pred"].sum())
        sub_y_true = sub["y_true"].values
        sub_y_pred = sub["y_pred"].values
        
        sub_prec = float(precision_score(sub_y_true, sub_y_pred, zero_division=0))
        sub_rec = float(recall_score(sub_y_true, sub_y_pred, zero_division=0))
        sub_f1 = float(f1_score(sub_y_true, sub_y_pred, zero_division=0))
        rate = round((det / tot) * 100, 1) if tot > 0 else 0.0

        fault_stats[ftype] = {
            "fault_category": ftype.replace("_", " ").title(),
            "total_injected": tot,
            "detected": det,
            "missed": tot - det,
            "detection_rate_pct": rate,
            "precision_pct": round(sub_prec * 100, 1),
            "recall_pct": round(sub_rec * 100, 1),
            "f1_score_pct": round(sub_f1 * 100, 1)
        }

    results = {
        "status": "completed",
        "evaluation_timestamp": datetime.now().isoformat(),
        "dataset": os.path.basename(dataset_path),
        "evaluated_samples": len(y_true_all),
        "total_anomalies_injected": int(sum(y_true_all)),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "avg_detection_latency_ms": round(avg_latency_ms, 3),
        "total_evaluation_time_sec": round(total_duration_sec, 2),
        "metrics": {
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "false_positive_rate": round(fpr * 100, 2)
        },
        "fault_type_breakdown": fault_stats
    }

    try:
        os.makedirs(os.path.dirname(METRICS_OUTPUT_PATH), exist_ok=True)
        with open(METRICS_OUTPUT_PATH, "w") as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save evaluation metrics JSON: {e}")

    return results

def get_latest_evaluation() -> Dict[str, Any]:
    """Retrieves cached evaluation metrics or runs a fresh evaluation if missing."""
    if os.path.exists(METRICS_OUTPUT_PATH):
        try:
            with open(METRICS_OUTPUT_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return run_evaluation()

def get_controlled_evaluation() -> Dict[str, Any]:
    """Retrieves Phase 5C controlled anomaly-injection evaluation metrics."""
    controlled_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evaluation", "evaluation_metrics.json")
    if os.path.exists(controlled_path):
        try:
            with open(controlled_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    from .controlled_evaluation import run_controlled_evaluation
    return run_controlled_evaluation()

