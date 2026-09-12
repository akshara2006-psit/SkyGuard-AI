<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=210&text=SKYGUARD%20AI&fontSize=52&fontColor=ffffff&fontAlignY=38&desc=Intelligent%20Real-Time%20Anomaly%20Detection%20for%20Automatic%20Weather%20Stations&descAlignY=60&descSize=18&animation=fadeIn&color=0:0f172a,50:075985,100:0284c7" width="100%" alt="SkyGuard AI">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=19&pause=1100&color=38BDF8&center=true&vCenter=true&width=850&lines=Detect+%E2%86%92+Explain+%E2%86%92+Assess+Health+%E2%86%92+Recommend+Action;Temperature+%7C+Pressure+%7C+Relative+Humidity;Real+weather+or+sensor+failure%3F+SkyGuard+decides.;Built+for+SIH+Problem+Statement+26073" alt="SkyGuard AI animated tagline">

<br>

<a href="https://skyguard-ai-1-2nro.onrender.com">
<img src="https://img.shields.io/badge/%F0%9F%9A%80%20LIVE%20DEMO-0f172a?style=for-the-badge&labelColor=0284c7" alt="Live Demo">
</a>
<a href="https://skyguard-ai-wsf9.onrender.com">
<img src="https://img.shields.io/badge/%E2%9A%99%EF%B8%8F%20BACKEND%20API-0f172a?style=for-the-badge&labelColor=059669" alt="Backend API">
</a>
<a href="https://github.com/akshara2006-psit/SkyGuard-AI">
<img src="https://img.shields.io/badge/%F0%9F%93%A6%20SOURCE%20CODE-0f172a?style=for-the-badge&labelColor=7c3aed" alt="Source Code">
</a>

<br><br>

<img src="https://img.shields.io/badge/SIH-PS%2026073-0284c7?style=flat-square" alt="SIH PS 26073">
<img src="https://img.shields.io/badge/NOAA-ASOS%20Real%20Data-0891b2?style=flat-square" alt="NOAA ASOS">
<img src="https://img.shields.io/badge/Frontend-React-06b6d4?style=flat-square&logo=react&logoColor=white" alt="React">
<img src="https://img.shields.io/badge/Backend-FastAPI-059669?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/ML-Isolation%20Forest-7c3aed?style=flat-square" alt="Isolation Forest">

</div>

🌦️ The problem

Automatic Weather Stations continuously produce observations that support forecasting, agriculture, disaster management, aviation and climate science.

But an unusual observation does not automatically mean bad weather.

It could be:

🌩️ a genuine meteorological event

🔧 a sensor malfunction

📈 a sudden spike

🧊 a frozen value

📉 calibration drift

📡 communication failure

🗃️ corrupted telemetry

SkyGuard AI asks one operational question:

Is this unusual observation real weather — or is the sensor/data stream failing?

🎯 What SkyGuard monitors

Sensor variable

Unit

Detection focus

🌡️ Temperature

°C

Spikes · Drift · Temporal anomalies

🧭 Atmospheric Pressure

hPa

Spikes · Frozen values · Drift

💧 Relative Humidity

%

Spikes · Frozen values · Drift

The implementation stays within the three variables specified by SIH PS 26073.

🧠 How it works

       AWS TELEMETRY
   T / P / RH observations
             │
             ▼
   ┌─────────────────────┐
   │ Validation &        │
   │ Preprocessing       │
   └──────────┬──────────┘
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
  Isolation  Temporal  Seasonal
   Forest    Analysis  Baseline
      │       │        │
      └───────┼────────┘
              ▼
      Multivariate
       Consistency
              │
              ▼
      Spatial Consistency
              │
              ▼
     ┌─────────────────┐
     │ Cause Classifier│
     └────────┬────────┘
              │
       ┌──────┼───────┐
       ▼      ▼       ▼
    NORMAL  WEATHER  SENSOR
            EVENT     FAULT
       │      │       │
       └──────┼───────┘
              ▼
   Confidence + Evidence
              │
       ┌──────┴──────┐
       ▼             ▼
   🚨 Alerts      ❤️ Health
       │             │
       └──────┬──────┘
              ▼
      🔧 Recommended Action

✨ What makes it different

SkyGuard is not simply a threshold checker.

It combines several evidence layers and turns them into an actionable sensor-health decision.

🔍 Multi-layer detection

Isolation Forest
Finds observations that look unusual compared with learned patterns.

Temporal analysis
Looks for spikes, persistence/frozen values, drift and missing telemetry.

Seasonal baseline
Accounts for hour-of-day and meteorological season before judging an observation.

Multivariate consistency
Checks whether temperature, pressure and humidity behave coherently together.

Spatial consistency
Uses observations from comparable nearby stations as supporting evidence.

Cause classification
Converts the combined evidence into:

NORMAL · POSSIBLE GENUINE WEATHER EVENT · PROBABLE SENSOR ANOMALY

🛰️ Real-world NOAA data

SkyGuard includes an ingestion adapter for the NOAA/NCEI 5-Minute Surface Weather Observations from the ASOS Network.

Current integrated data





🌐 NOAA stations

8

📡 NOAA observations

13,756

🏠 Simulation stations

6

🛰️ Total dashboard stations

14

📍 Observation interval

5 minutes

NOAA stations currently represented include:

KATL · KBOS · KDEN · KDFW · KJFK · KLAX · KORD · KSFO

The real-data path is kept separate from the simulation network so the dashboard can distinguish NOAA ASOS observations from simulation data.

🖥️ Dashboard

<div align="center">

Overview

<img src="docs/assets/dashboard.png" width="94%" alt="SkyGuard AI Dashboard">

</div>

Built-in views

View

Purpose

📊 Overview

Network health, anomalies and active alerts

🛰️ Stations

Station-level telemetry and health

🚨 Alerts

Severity, evidence and recommended action

📈 Analytics

Model benchmark and performance information

🧪 Simulation

Controlled fault scenarios

ℹ️ About

SIH problem, mission and system information

🚨 Fault scenarios

The simulation module demonstrates the complete detection pipeline:

NORMAL
   ↓
TEMPERATURE SPIKE
   ↓
FROZEN HUMIDITY
   ↓
SENSOR DRIFT
   ↓
COMMUNICATION FAILURE
   ↓
GENUINE WEATHER EVENT
   ↓
MULTIVARIATE INCONSISTENCY

Each scenario passes through the same analysis pipeline rather than being a UI-only animation.

📊 Controlled evaluation

SkyGuard contains a separate controlled evaluation pipeline with deterministic fault injection.

The benchmark uses 1,000 observations:

182 injected sensor anomalies

22 genuine-weather cases

796 clean normal observations

Results

Metric

Result

Precision

26.36%

Recall

47.80%

F1 Score

33.98%

False Positive Rate

29.71%

False Negative Rate

52.20%

Genuine-weather discrimination

95.45% (21/22)

Detection by fault category

Fault

Result

🌡️ Temperature spikes

4/4 · 100%

🧭 Pressure spikes

4/4 · 100%

💧 Humidity spikes

4/4 · 100%

📡 Missing telemetry

15/18 · 83.3%

🔗 Multivariate inconsistency

11/16 · 68.8%

🧊 Frozen values

41/64 · 64.1%

📉 Drift injections

8/72 · 11.1%

Important: these are controlled evaluation results. They are not presented as universal real-world accuracy. Unlabeled NOAA observations are not treated as ground truth.

⚡ Real-time performance

Test

Measured result

Single observation · mean

63.55 ms

Single observation · P95

76.24 ms

Single observation · P99

84.34 ms

Batch of 50

45.6 obs/sec

Batch of 100

45.8 obs/sec

Batch of 200

40.7 obs/sec

Peak inference heap overhead

0.47 MB

❤️ Sensor health

SkyGuard does not stop at saying “anomaly detected.”

It maintains a sensor-health view using:

anomaly evidence

missing telemetry

detected fault signals

degradation trend

recent behaviour

maintenance recommendations

This turns anomaly detection into an operational decision-support system.

🔬 Explainability

For every important anomaly, SkyGuard can expose evidence such as:

Observed value
      ↓
Expected / baseline value
      ↓
Anomaly score
      ↓
Temporal evidence
      ↓
Multivariate evidence
      ↓
Spatial evidence
      ↓
Seasonal evidence
      ↓
Feature attribution
      ↓
Cause + confidence
      ↓
Recommended action

The current implementation uses model decision-path feature attribution rather than claiming a formal SHAP implementation.

🛠️ Technology

<div align="center">

Layer

Technology

🎨 Frontend

React · Vite · Recharts · Lucide React

⚙️ Backend

Python · FastAPI · SQLAlchemy · Pydantic

🧠 ML

scikit-learn · Isolation Forest · NumPy · pandas

🗄️ Database

SQLite

🌐 Real data

NOAA/NCEI ASOS

🚀 Deployment

GitHub · Render

</div>

📁 Project structure

SkyGuard-AI/
│
├── backend/
│   ├── app/
│   │   ├── adapters/
│   │   ├── api/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── services/
│   │   ├── database/
│   │   └── main.py
│   │
│   ├── data/
│   │   ├── evaluation/
│   │   └── noaa_asos/
│   ├── scripts/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   └── assets/
│       └── dashboard.png
│
├── data/
├── PROJECT_STATUS.md
├── SIH_READINESS_AUDIT.md
├── README.md
└── .gitignore

🚀 Run locally

1. Start the backend

cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

2. Start the frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173

3. Environment variables

VITE_API_BASE_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=your_google_web_client_id

🌍 Live deployment

<div align="center">

🚀 SkyGuard AI is deployed

Frontend

https://skyguard-ai-1-2nro.onrender.com

Backend

https://skyguard-ai-wsf9.onrender.com

Source

https://github.com/akshara2006-psit/SkyGuard-AI

</div>

🎯 SIH PS 26073

Problem Statement: 26073
Organization: Ministry of Earth Sciences

SIH requirement

SkyGuard implementation

Temperature / Pressure / RH

✅

Real-time anomaly detection

✅

Sensor spikes

✅

Frozen values

✅

Communication failures

✅

Sensor drift

✅

Temporal analysis

✅

Seasonal / diurnal baseline

✅

Multivariate consistency

✅

Spatial consistency

✅

Genuine weather discrimination

✅

Severity

✅

Confidence

✅

Explainability

✅

Root-cause classification

✅

Sensor health

✅

Maintenance recommendation

✅

Optional corrected values

✅

NOAA real-world data

✅

Controlled simulation

✅

Executable deployment

✅

⚠️ Engineering limitations

SkyGuard is intentionally documented with measured limitations rather than overstating the prototype.

Drift detection is weaker than spike detection in the controlled benchmark.

Complete ground-truth labels are unavailable for the real NOAA observations.

External SMS/email/webhook alert delivery is not included in the current prototype.

Native ESP32 firmware and physical energy measurements remain deployment extensions.

The current deployment is a single-service prototype architecture rather than a distributed Kafka/Celery production cluster.

Explainability currently uses decision-path feature attribution rather than a formal SHAP dependency.

📚 Research foundation

The project is informed by established meteorological quality-control approaches involving:

range and validity checks

temporal consistency

persistence/frozen-value detection

internal consistency

spatial consistency

automated weather-station validation

machine-learning anomaly detection

explainable anomaly analysis

Key references include work from WMO, NOAA/NCEI, and peer-reviewed meteorological quality-control and anomaly-detection literature.

🌤️ The vision

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=21&pause=1200&color=38BDF8&center=true&vCenter=true&width=800&lines=A+weather+station+should+not+only+measure.;It+should+know+when+its+measurement+can+be+trusted." alt="Animated vision">

<br><br>

DETECT → EXPLAIN → ASSESS HEALTH → RECOMMEND ACTION → RECOVER

<br><br>

<img src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer&animation=fadeIn&color=0:0284c7,50:075985,100:0f172a" width="100%" alt="SkyGuard footer">

<strong>Built for Smart India Hackathon · PS 26073 · Ministry of Earth Sciences</strong>

</div>