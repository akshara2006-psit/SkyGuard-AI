# SkyGuard AI — Controlled Anomaly-Injection Evaluation Report
**Evaluation Date**: 2026-09-09T18:48:32.457147  
**Evaluation Type**: Controlled anomaly-injection evaluation  
**Pipeline**: SkyGuard AI Master Pipeline (Isolation Forest, TemporalAnalyzer, SeasonalBaseline, Multivariate, Spatial, CauseClassifier, ValueCorrector)  

> [!NOTE]
> **Methodological Scope**: These metrics reflect controlled anomaly injection against known ground-truth labels on a representative sample of AWS telemetry. They do NOT represent claimed unbounded real-world field accuracy.

---

## 1. Executive Summary

- **Total Observations Evaluated**: 1000
- **Stations Evaluated**: AWS-001, AWS-002
- **Sensor Anomaly Injected Samples**: 182
- **Genuine Weather Injected Samples**: 22
- **Clean Normal Samples**: 796
- **Total Runtime**: 28.1 seconds (35.6 observations/sec)
- **Average Ingestion Latency**: 28.096 ms/observation

---

## 2. Overall Sensor Fault Detection Performance

| Metric | Measured Value | Definition |
|---|---|---|
| **True Positives (TP)** | **87** | Injected sensor faults correctly flagged |
| **False Positives (FP)** | **243** | Non-fault observations diagnosed as sensor faults |
| **True Negatives (TN)** | **575** | Non-fault observations correctly diagnosed (Normal or Weather) |
| **False Negatives (FN)** | **95** | Injected sensor faults missed by the pipeline |
| **Precision** | **26.36%** | TP / (TP + FP) |
| **Recall (Detection Rate)** | **47.8%** | TP / (TP + FN) |
| **F1-Score** | **33.98%** | Harmonic mean of Precision & Recall |
| **False Positive Rate (FPR)** | **29.71%** | FP / (FP + TN) |
| **False Negative Rate (FNR)** | **52.2%** | FN / (FN + TP) |

---

## 3. Anomaly Type Breakdown

| Anomaly Category | Injected Samples | Detected | Missed | Detection Rate | Primary Diagnostic Classifications |
|---|---|---|---|---|---|
| `frozen_sensor` | 64 | 41 | 23 | **64.1%** | PROBABLE_SENSOR_ANOMALY: 41, NORMAL: 14, POSSIBLE_GENUINE_WEATHER_EVENT: 9 |
| `genuine_weather_event` | 22 | 1 | 21 | **4.5%** | POSSIBLE_GENUINE_WEATHER_EVENT: 21, PROBABLE_SENSOR_ANOMALY: 1 |
| `humidity_spike` | 4 | 4 | 0 | **100.0%** | PROBABLE_SENSOR_ANOMALY: 4 |
| `missing_telemetry` | 18 | 15 | 3 | **83.3%** | POSSIBLE_COMMUNICATION_FAILURE: 9, POSSIBLE_DATA_QUALITY_ISSUE: 6, POSSIBLE_GENUINE_WEATHER_EVENT: 3 |
| `multivariate_inconsistency` | 16 | 11 | 5 | **68.8%** | PROBABLE_SENSOR_ANOMALY: 11, POSSIBLE_GENUINE_WEATHER_EVENT: 5 |
| `normal` | 796 | 242 | 554 | **30.4%** | POSSIBLE_GENUINE_WEATHER_EVENT: 330, PROBABLE_SENSOR_ANOMALY: 242, NORMAL: 224 |
| `pressure_spike` | 4 | 4 | 0 | **100.0%** | PROBABLE_SENSOR_ANOMALY: 4 |
| `sensor_drift` | 72 | 8 | 64 | **11.1%** | POSSIBLE_GENUINE_WEATHER_EVENT: 40, NORMAL: 24, PROBABLE_SENSOR_ANOMALY: 8 |
| `temperature_spike` | 4 | 4 | 0 | **100.0%** | PROBABLE_SENSOR_ANOMALY: 4 |

---

## 4. Sensor Type Breakdown

| Sensor Type | Injected Faults | Detected | Detection Rate |
|---|---|---|---|
| `all` | 18 | 15 | **83.3%** |
| `humidity` | 46 | 23 | **50.0%** |
| `pressure` | 38 | 9 | **23.7%** |
| `temperature` | 80 | 40 | **50.0%** |

---

## 5. Genuine Weather Event Discriminative Evaluation

The objective is to verify that SkyGuard AI distinguishes coordinated atmospheric variations (fronts, storms, airmass shifts) from isolated hardware sensor malfunctions.

- **Total Injected Genuine Events**: 22
- **Correctly Classified as Genuine Weather Event (`POSSIBLE_GENUINE_WEATHER_EVENT`)**: **21 (95.45%)**
- **Incorrectly Misclassified as Sensor Malfunction (`PROBABLE_SENSOR_ANOMALY`)**: **1 (4.55%)**
- **Classified as Normal Baseline**: 0

---

## 6. Runtime Performance & Computational Efficiency

- **Total Observations Processed**: 1000
- **Wall-Clock Duration**: 28.1 seconds
- **Throughput**: 35.6 observations/second
- **Mean Processing Latency**: 28.096 ms/observation

---

## 7. Limitations & Honest Assessment

1. **Synthetic & Controlled Context**: Evaluated on controlled injections on representative AWS telemetry; real sensor degradation exhibits broader mechanical and environmental nuances.
2. **Drift & Multi-Sensor Interaction**: Sensor drift on one parameter during natural diurnal shifts in companion channels is occasionally classified as a meteorological event if background diurnal drift is non-negligible.
3. **Database Integrity**: The evaluation executed entirely in-memory and through isolated files. Zero production SQLite tables were modified.
