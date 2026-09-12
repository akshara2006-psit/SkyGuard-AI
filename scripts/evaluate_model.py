"""
SkyGuard AI - High-Performance Model Evaluation & Benchmark
Evaluates the anomaly detection and cause classification pipeline across all stations.
"""
import pandas as pd
import numpy as np
import os
import json
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.ml.preprocessor import preprocess_station_data, prepare_features_for_model
from app.ml.isolation_forest import SkyGuardIsolationForest
from app.ml.temporal_analyzer import TemporalAnalyzer
from app.ml.multivariate_analyzer import MultivariateAnalyzer
from app.ml.cause_classifier import CauseClassifier

def evaluate_pipeline():
    benchmark_path = "data/processed/benchmark_dataset_with_ground_truth.csv"
    if not os.path.exists(benchmark_path):
        print("Generating benchmark data...")
        from inject_faults import process_all
        process_all()

    df = pd.read_csv(benchmark_path)
    print(f"Loading benchmark dataset: {len(df)} records across {df['station_id'].nunique()} stations.")

    y_true_all = []
    y_pred_all = []
    fault_type_all = []

    temporal = TemporalAnalyzer()
    multivariate = MultivariateAnalyzer()
    classifier = CauseClassifier()

    for station_id, group in df.groupby("station_id"):
        group = group.reset_index(drop=True)
        # 1. Preprocess full station series
        processed_df = preprocess_station_data(group.to_dict(orient="records"), station_id)
        
        # 2. Train Isolation Forest on normal baseline (first 500 records)
        train_df = processed_df.iloc[:500]
        X_train, feature_names = prepare_features_for_model(train_df)
        model = SkyGuardIsolationForest(n_estimators=100, contamination=0.04)
        model.fit(X_train, feature_names)

        # 3. Score all records
        X_all, _ = prepare_features_for_model(processed_df)
        scores = model.predict_scores(X_all)

        # 4. Temporal & Diagnostic checks per record
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
            fault_type_all.append(group.loc[i, "fault_type"])

    precision = float(precision_score(y_true_all, y_pred_all, zero_division=0))
    recall = float(recall_score(y_true_all, y_pred_all, zero_division=0))
    f1 = float(f1_score(y_true_all, y_pred_all, zero_division=0))
    tn, fp, fn, tp = confusion_matrix(y_true_all, y_pred_all).ravel()
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
        rate = round((det / tot) * 100, 1) if tot > 0 else 0.0
        fault_stats[ftype] = {
            "total": tot,
            "detected": det,
            "missed": tot - det,
            "detection_rate_pct": rate
        }

    results = {
        "dataset_samples": len(y_true_all),
        "total_anomalies_injected": int(sum(y_true_all)),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "metrics": {
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "false_positive_rate": round(fpr * 100, 2)
        },
        "fault_type_breakdown": fault_stats
    }

    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/model_evaluation_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n================ SKYGUARD AI MODEL BENCHMARK ================")
    print(f"Total Observations Tested: {results['dataset_samples']}")
    print(f"Precision:                 {results['metrics']['precision']}%")
    print(f"Recall:                    {results['metrics']['recall']}%")
    print(f"F1 Score:                  {results['metrics']['f1_score']}%")
    print(f"False Positive Rate (FPR): {results['metrics']['false_positive_rate']}%")
    print("\nFault Detection Breakdown:")
    for k, v in fault_stats.items():
        print(f"  * {k:<25}: {v['detected']}/{v['total']} ({v['detection_rate_pct']}%)")
    print("============================================================\n")

if __name__ == "__main__":
    evaluate_pipeline()
