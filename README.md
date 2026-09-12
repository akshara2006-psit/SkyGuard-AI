::: {align="center"}

🌦️ SkyGuard AI

Intelligent Real-Time Anomaly Detection for Automatic Weather Stations

<p>

<img src="https://img.shields.io/badge/SIH-2025%20%7C%20PS%2026073-0ea5e9?style=for-the-badge&logo=cloud&logoColor=white" alt="SIH PS 26073"/>{=html}
<img src="https://img.shields.io/badge/AI%2FML-Anomaly%20Detection-7c3aed?style=for-the-badge" alt="AI ML"/>{=html}
<img src="https://img.shields.io/badge/Data-NOAA%20ASOS-0284c7?style=for-the-badge" alt="NOAA ASOS"/>{=html}
<img src="https://img.shields.io/badge/Backend-FastAPI-059669?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>{=html}
<img src="https://img.shields.io/badge/Frontend-React-06b6d4?style=for-the-badge&logo=react&logoColor=white" alt="React"/>{=html}

</p>

<img src="https://readme-typing-svg.demolab.com?font=Inter&weight=700&size=22&pause=900&color=38BDF8&center=true&vCenter=true&width=850&lines=Detect+sensor+faults+before+they+become+bad+decisions.;Separate+real+weather+events+from+sensor+anomalies.;Monitor+Temperature+%7C+Pressure+%7C+Relative+Humidity.;From+raw+AWS+observations+to+actionable+alerts." alt="Animated tagline"/>{=html}

<br/>{=html}

SkyGuard AI turns Automatic Weather Station telemetry into an
explainable, real-time sensor-health decision system.

🚀 Live Demo · ⚙️ Backend
API · 📦
GitHub
:::

🛰️ What is SkyGuard AI?

Automatic Weather Stations (AWS) continuously provide observations used
in forecasting, agriculture, disaster management, aviation and climate
science. But a strange observation is not always bad data: it may be a
genuine meteorological event, a sensor fault, a frozen value, a
communication failure, calibration drift, or corrupted telemetry.

SkyGuard AI is designed to answer the operational question:

"Is this unusual observation real weather, or is the sensor/data
stream failing?"

The system focuses strictly on the three SIH PS 26073 variables:

Variable                Unit                    What SkyGuard watches

🌡️ Temperature          °C                      spikes, drift, abnormal
behaviour

🧭 Atmospheric Pressure hPa                     spikes,
persistence/frozen
behaviour, drift

✨ Why it is different

Traditional quality control can identify values outside simple
thresholds. SkyGuard combines multiple evidence layers instead of
relying on one rule.

                 ┌───────────────────────────────┐
                 │      AWS OBSERVATIONS          │
                 │   Temperature / Pressure / RH │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │     MULTI-LAYER ANALYSIS      │
                 │                               │
                 │  • Isolation Forest           │
                 │  • Temporal / spike checks    │
                 │  • Frozen-value detection     │
                 │  • Drift analysis             │
                 │  • Seasonal baseline          │
                 │  • Multivariate consistency   │
                 │  • Spatial consistency        │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │   EXPLAINABLE DECISION        │
                 │                               │
                 │  NORMAL                       │
                 │  POSSIBLE GENUINE WEATHER     │
                 │  PROBABLE SENSOR ANOMALY      │
                 └───────────────┬───────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        🚨 Alert            ❤️ Health         🔧 Action
        Severity            Degradation       Maintenance
        Confidence          Trend             Recommendation

🎯 Core capabilities

🔍 Real-time anomaly detection

Detects abnormal AWS observations using an ensemble of ML and
deterministic signals.

📈 Temporal intelligence

Looks for: - sudden spikes - persistent/frozen values - linear sensor
drift - missing telemetry

🌦️ Genuine-weather discrimination

A coordinated change across meteorological variables can be treated
differently from an isolated sensor failure.

🧩 Multivariate consistency

Temperature, pressure and humidity are evaluated together rather than
independently.

🗺️ Spatial consistency

Nearby stations can provide supporting evidence when observations are
available at comparable timestamps.

🧠 Explainable decisions

Each anomaly can expose evidence such as: - anomaly score - temporal
flags - multivariate evidence - spatial consistency - observed vs
expected values - feature attribution / decision-path evidence

❤️ Sensor health

SkyGuard maintains a health index and degradation trend to help
prioritize maintenance.

🔧 Corrected / imputed values

Where supported by available evidence, the system can produce query-time
corrected values while keeping the raw observation immutable.

🧪 Fault simulation

Built-in scenarios demonstrate: - Normal - Temperature spike - Frozen
humidity - Sensor drift - Communication failure - Genuine weather
event - Multivariate inconsistency

📡 Real-world data

SkyGuard includes a real-data ingestion path for the NOAA/NCEI
5-Minute Surface Weather Observations from the ASOS Network.

Current integrated prototype data:

8 NOAA ASOS stations

13,756 real-world NOAA observations

5-minute observation source

Temperature, pressure and relative humidity derived/handled by the
ingestion adapter

Missing-value handling

Raw source caching and provenance documentation

Example integrated stations include:

KATL · KBOS · KDEN · KDFW · KJFK · KLAX · KORD · KSFO

The production prototype also retains 6 simulation stations, giving
the deployed dashboard 14 stations in total.

🖥️ Live dashboard

::: {align="center"}
<img src="docs/assets/dashboard.png" alt="SkyGuard AI live dashboard" width="95%"/>{=html}
:::

Tip: Add your latest dashboard screenshot at
docs/assets/dashboard.png to display it here. The screenshot should
show the live Overview page with the station cards and alert center.

Dashboard includes

Overview · Stations · Alerts · Analytics ·
Simulation · About

The live dashboard currently displays the deployed network, station
health, alerts and anomaly evidence.

📊 Evaluation

SkyGuard includes a separate controlled evaluation pipeline using
deterministic fault injection rather than claiming performance from
unlabeled real-world observations.

Controlled evaluation --- 1,000 observations

Metric                                         Result

Precision                                  26.36%
Recall                                     47.80%
F1 Score                                   33.98%
False Positive Rate                        29.71%
False Negative Rate                        52.20%
Genuine-weather discrimination     95.45% (21/22)

Category-level detection

Fault category                           Detection

Temperature spikes                4/4 --- 100%
Pressure spikes                   4/4 --- 100%
Humidity spikes                   4/4 --- 100%
Missing telemetry              15/18 --- 83.3%
Multivariate inconsistency     11/16 --- 68.8%
Frozen values                  41/64 --- 64.1%
Drift injections                8/72 --- 11.1%

Important: These are controlled evaluation results on an injected
dataset, not a claim that SkyGuard has this accuracy on all real-world
weather observations. Real NOAA observations do not provide complete
ground-truth fault labels.

⚡ Performance

The real-time inference benchmark measured:

Benchmark                                           Result

Single observation --- mean                   63.55 ms
Single observation --- P95                    76.24 ms
Single observation --- P99                    84.34 ms
Batch 50                         45.6 observations/sec
Batch 100                        45.8 observations/sec
Batch 200                        40.7 observations/sec
Peak inference heap overhead                   0.47 MB

The pipeline is designed for incremental/stateless observation
processing, making it suitable for deployment behind a streaming or
gateway layer.

🧠 Machine-learning pipeline

Raw telemetry
     │
     ▼
Validation & preprocessing
     │
     ├──────────────► Isolation Forest
     │
     ├──────────────► Temporal analysis
     │                    ├─ Z-score spikes
     │                    ├─ Frozen values
     │                    └─ Drift
     │
     ├──────────────► Seasonal baseline
     │
     ├──────────────► Multivariate consistency
     │
     └──────────────► Spatial consistency
                            │
                            ▼
                    Cause classification
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          NORMAL       WEATHER EVENT    SENSOR FAULT
                            │
                            ▼
              Confidence + Explanation
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
            Alert engine          Sensor health

🧰 Technology stack

Frontend

React

Vite

Recharts

Lucide React

Axios

Backend

Python

FastAPI

SQLAlchemy

SQLite

Pydantic

AI / ML

scikit-learn

Isolation Forest

NumPy

pandas

Temporal anomaly analysis

Seasonal baselines

Multivariate consistency analysis

Spatial consistency analysis

Deployment

Render

GitHub

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
│   │   ├── config.py
│   │   ├── database/
│   │   └── main.py
│   │
│   ├── data/
│   │   ├── evaluation/
│   │   └── noaa_asos/
│   │
│   ├── scripts/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   └── assets/
│       └── dashboard.png
│
├── data/
├── PROJECT_STATUS.md
├── README.md
└── .gitignore

🚀 Run locally

1. Clone

git clone https://github.com/akshara2006-psit/SkyGuard-AI.git
cd SkyGuard-AI

2. Backend

cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

3. Frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173

For local Google authentication, configure the frontend environment
variable:

VITE_GOOGLE_CLIENT_ID=your_google_web_client_id
VITE_API_BASE_URL=http://localhost:8000/api

For the deployed frontend, VITE_API_BASE_URL should point to the
deployed backend API.

🌐 Deployed architecture

                         INTERNET
                            │
                            ▼
              ┌─────────────────────────┐
              │   React / Vite Frontend  │
              │        Render            │
              └────────────┬────────────┘
                           │ HTTPS / REST
                           ▼
              ┌─────────────────────────┐
              │      FastAPI Backend     │
              │         Render           │
              └────────────┬────────────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
          SQLite DB     ML Pipeline    NOAA Adapter
              │            │             │
              ▼            ▼             ▼
          Stations      Decisions     ASOS Data
          Alerts        Evidence      Real Data
          Health

🔐 Authentication

The web dashboard supports Google Sign-In through Google Identity
Services, with a Demo Mode fallback for development/testing.

For production OAuth configuration, the deployed Render hostname must be
registered as an authorized JavaScript origin for the same Web OAuth
client ID used by the frontend.

📚 Research & references

SkyGuard's design is informed by established meteorological
quality-control and anomaly-detection research.

World Meteorological Organization (WMO) --- World Meteorological
Day 2026: observing systems and surface observations
https://public.wmo.int/site/world-meteorological-day-2026/how-does-observing-system-work

WMO --- Recognition criteria for meteorological observing
stations and quality control
https://public.wmo.int/recognition-criteria-meteorological-observing-stations

WMO WDQMS --- WIGOS Data Quality Monitoring System
https://wdqms.wmo.int/about

Estévez, J. et al. (2011), Guidelines on validation procedures for
meteorological data from automatic weather stations, Journal of
Hydrology.
DOI: https://doi.org/10.1016/j.jhydrol.2011.02.031

Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008), Isolation Forest,
IEEE ICDM.
DOI: https://doi.org/10.1109/ICDM.2008.17

Chandola, V., Banerjee, A., & Kumar, V. (2009), Anomaly Detection:
A Survey, ACM Computing Surveys.
DOI: https://doi.org/10.1145/1541880.1541882

Patro, S. & Bartakke (2025), AWS quality-control study in Pune
District.
DOI: https://doi.org/10.1109/ICORT64008.2025.11115447

🎯 SIH PS 26073 alignment

Problem Statement: 26073
Title: AI/ML-Based Intelligent Anomaly Detection for Automatic
Weather Stations
Organization: Ministry of Earth Sciences

SIH requirement               SkyGuard implementation

Temperature / Pressure / RH   ✅ Strict three-variable scope
Real-time detection           ✅ REST + simulation streaming
Spikes                        ✅
Frozen values                 ✅
Communication failures        ✅
Sensor drift                  ✅
Temporal patterns             ✅
Seasonal/diurnal baseline     ✅
Multivariate consistency      ✅
Spatial consistency           ✅
Genuine weather vs fault      ✅
Severity & confidence         ✅
Explainability                ✅ Decision-path evidence
Root-cause classification     ✅
Sensor health                 ✅
Maintenance guidance          ✅
Corrected values              ✅ Optional
Real-world data               ✅ NOAA ASOS
Simulation                    ✅ Controlled fault scenarios
Dashboard                     ✅ React dashboard

⚠️ Current limitations

SkyGuard is an executable prototype and documents its limitations rather
than hiding them.

The controlled evaluation uses injected labels; unlabeled real NOAA
data is not treated as ground truth.

Drift detection is currently weaker than spike/frozen-value
detection in the controlled benchmark.

The current spatial analysis uses a configurable implementation
radius and should not be interpreted as a universal meteorological
neighbourhood rule.

External SMS/email/webhook alert delivery is not part of the current
prototype.

Native ESP32 firmware and physical power measurements are future
deployment work.

The current deployment uses a single Render service/database
architecture rather than a distributed Kafka/Celery-style production
cluster.

Feature attribution uses model decision-path evidence; a formal SHAP
dependency is not required for the current implementation.

🏆 The bigger vision

SkyGuard AI is built around a larger idea:

A weather observation network should not only report measurements
--- it should understand when those measurements can be trusted.

The long-term vision is a self-aware, self-healing weather observation
network that can:

Detect → Explain → Assess health → Recommend action → Recover

::: {align="center"}

🌤️ From weather observations to trustworthy intelligence.

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,50:0369a1,100:38bdf8&height=120&section=footer&animation=fadeIn" alt="SkyGuard footer"/>{=html}

Built for Smart India Hackathon · Problem Statement 26073

⭐ If SkyGuard AI is useful or interesting, consider starring the
repository.
:::
