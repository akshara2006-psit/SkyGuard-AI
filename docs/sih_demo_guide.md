# SkyGuard AI — Evaluator Demonstration & Walkthrough Guide

## Presentation Duration: 5 - 7 Minutes

### Step 1: Context & Problem Statement (1 Minute)
- **Opening Statement**: *"Good morning / afternoon evaluators. We are presenting SkyGuard AI for Problem Statement 26073 — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations."*
- **Core Positioning**: *"Weather forecasts directly impact aviation, agriculture, and disaster management. But before we trust the weather forecast, SkyGuard asks: **can we trust the incoming AWS sensor data?**"*
- **The Challenge**: Traditional threshold alerts fail when sensors freeze, drift slowly, or when genuine severe weather is mistaken for sensor failure. The system operates strictly within the official input scope: Temperature (°C), Atmospheric Pressure (hPa), and Relative Humidity (%).

### Step 2: System Architecture & Live Network Overview (1 Minute)
- Open `http://localhost:5173`.
- Show the 6 real-world Indian AWS stations (Delhi Safdarjung, Mumbai Colaba, Chennai Nungambakkam, Kolkata Alipore, Bengaluru HAL, Hyderabad Begumpet).
- Click **Start Simulation** to demonstrate the live telemetry ingest pipeline updating every 3 seconds.

### Step 3: Demonstrating Scenario 2 — Temperature Sensor Spike (1.5 Minutes)
- In the **Simulation Lab** panel, click **Temp Spike (AWS-001)**.
- Select `AWS-001` in the station list.
- **Show Evaluators**:
  1. The **Diagnostic Banner** instantly turns Red (`PROBABLE_SENSOR_ANOMALY`).
  2. **Observed vs AI-Estimated Expected Value**: Point out observed value vs AI-estimated expected baseline.
  3. **Anomaly Score vs Confidence**: Anomaly Score and Diagnostic Confidence are calculated dynamically.
  4. **Model Feature Attribution**: Point out feature attributions explaining the anomaly decision.
  5. **Spatial Consistency**: Shows nearby station comparison supporting localized fault.
  6. **Recommended Action**: *"Inspect temperature transducer for electrical noise, grounding issues, or impulse damage."*

### Step 4: The Crucial Differentiator — Genuine Weather Event (1.5 Minutes)
- In the Simulation Lab panel, click **Genuine Weather Event (AWS-005)**.
- Select `AWS-005 (Bengaluru HAL)`.
- **Key Demo Highlight**:
  - Point out that all three parameters shifted coherently (simultaneous temperature drop, barometric pressure drop, humidity surge).
  - Show that SkyGuard AI **does NOT falsely blame the sensors**.
  - The badge turns Cyan (`POSSIBLE_GENUINE_WEATHER_EVENT`), and the explanation states multi-sensor coherence aligning with a genuine meteorological event (e.g. frontal passage).

### Step 5: Sensor Health Degradation & Alert Operations (1 Minute)
- Show how repeated anomalies decrease the **Sensor Health Index** deterministically from 100% down to Warning or Degraded status with maintenance recommendations.
- Switch to the **Alerts** tab and demonstrate acknowledging active alerts.
- Switch to the **Incident Timeline** to show the historical trace of all detected events.

### Step 6: Dynamic Model Evaluation & Benchmark (1 Minute)
- Click the **Model Benchmark** button in the navbar (or open the **Analytics** view).
- Click **Run Live Benchmark** to execute dynamic pipeline evaluation across the ground-truth labelled benchmark dataset.
- Point out dynamic Precision, Recall (Sensitivity), F1-Score, False Positive Rate, and measured inference execution latency (ms/reading).
- Conclude: *"SkyGuard AI provides an explainable, reliable, and deployable data quality-control layer for automatic weather station networks."*
