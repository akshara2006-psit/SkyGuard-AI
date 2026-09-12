# SkyGuard AI — Technical Architecture & ML Specification

## 1. Executive Summary
SkyGuard AI is built on the principle that before downstream meteorologists or automated forecasting models consume Automatic Weather Station (AWS) observations, an autonomous quality-control layer must validate data authenticity, detect hardware transducer failures, and distinguish sensor anomalies from genuine meteorological phenomena.

## 2. Multi-Tier Diagnostic Pipeline

```
[AWS Observation: Temp, Pres, Hum, Timestamp]
                   │
                   ▼
       1. Physical Range Validation
          - Temp: [-50°C, 60°C]
          - Pressure: [850 hPa, 1085 hPa]
          - Humidity: [0%, 100%]
                   │
                   ▼
       2. Temporal Feature Extraction
          - Rolling short-term baseline (6-step) & long-term baseline (24-step)
          - Rate of change (1st & 3rd difference)
          - Persistence / Zero-variance index
          - Cross-parameter gradients (ΔT vs ΔP, Temp-Humidity ratio)
                   │
                   ▼
       3. Machine Learning Core (Isolation Forest)
          - 100 Isolation Trees, multi-dimensional feature space
          - Score normalization: Inverts raw negative scores into calibrated [0.0, 1.0] interval
                   │
                   ▼
       4. Temporal Rule Heuristics
          - Spike Detector: |x_t - μ_{recent}| > 3.5 σ
          - Freeze Detector: σ_{recent} < 0.05 over 6 consecutive intervals
          - Drift Detector: |Linear Regression Slope| > 0.25 units/step with R² > 0.5
          - Telemetry Dropout: Consecutive missing packet detector
                   │
                   ▼
       5. Multivariate Coherence Analysis
          - Computes normalized rates of change across all 3 channels simultaneously
          - Coherent multi-sensor shift (ΔT + ΔP + ΔH) -> High Meteorological Likelihood
          - Isolated single-sensor shift (ΔT only, with stable P and H) -> High Sensor Fault Likelihood
                   │
                   ▼
       6. Diagnostic Cause Classifier & Confidence Calculator
          - Combines ML Anomaly Score + Temporal Evidence + Multivariate Coherence
          - Outputs: NORMAL, PROBABLE_SENSOR_FAULT, POSSIBLE_WEATHER_EVENT, POSSIBLE_COMMUNICATION_FAILURE
                   │
                   ▼
       7. Sensor Health & Degradation Engine
          - Transparent formula: 100 - (Anomaly Rate × 35) - (Missing Rate × 25) - (Historical Faults × 1.2)
```

## 3. Separation of Anomaly Score vs Diagnostic Confidence
- **Anomaly Score (0 - 100%)**: Quantifies the statistical rarity or unexpectedness of the incoming sensor vector compared to historical diurnal distributions.
- **Diagnostic Confidence (0 - 100%)**: Measures the degree of agreement across independent diagnostic layers (e.g. IF anomaly + 4-sigma temperature spike + flat pressure/humidity lines = 94% confidence of a localized temperature sensor fault).

## 4. Non-Destructive AI-Estimated Expected Values
When an anomaly occurs (e.g. Temperature spikes to 68.0°C), SkyGuard AI **never** overwrites the raw observation. Both `observed_value` and `expected_value` (derived from recent background baseline models) are preserved for complete operational traceability.
