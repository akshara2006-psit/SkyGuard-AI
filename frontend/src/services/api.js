import axios from "axios";

// const API_BASE = "http://localhost:8000/api";
const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

export const fetchSummary = async () => {
  const res = await api.get("/summary");
  return res.data;
};

export const fetchStations = async () => {
  const res = await api.get("/stations");
  return res.data;
};

export const fetchStationDetail = async (stationId) => {
  const res = await api.get(`/stations/${stationId}`);
  return res.data;
};

export const fetchReadings = async (stationId, limit = 60) => {
  const res = await api.get(`/stations/${stationId}/readings?limit=${limit}`);
  return res.data;
};

export const fetchAnomalies = async (stationId = null, limit = 50) => {
  const url = stationId ? `/stations/${stationId}/anomalies?limit=${limit}` : `/anomalies?limit=${limit}`;
  const res = await api.get(url);
  return res.data;
};

export const fetchStationHealth = async (stationId) => {
  const res = await api.get(`/stations/${stationId}/health`);
  return res.data;
};

export const fetchAlerts = async (status = null) => {
  const url = status ? `/alerts?status=${status}` : "/alerts";
  const res = await api.get(url);
  return res.data;
};

export const acknowledgeAlert = async (alertId) => {
  const res = await api.post(`/alerts/${alertId}/acknowledge`);
  return res.data;
};

export const analyzeManualReading = async (payload) => {
  const res = await api.post("/analyze", payload);
  return res.data;
};

// Simulation APIs
export const fetchSimulationStatus = async () => {
  const res = await api.get("/simulation/status");
  return res.data;
};

export const startSimulation = async () => {
  const res = await api.post("/simulation/start");
  return res.data;
};

export const stopSimulation = async () => {
  const res = await api.post("/simulation/stop");
  return res.data;
};

export const injectSimulationFault = async (stationId, faultType, duration = 8) => {
  const res = await api.post("/simulation/inject", {
    station_id: stationId,
    fault_type: faultType,
    duration: duration,
  });
  return res.data;
};

export const triggerScenario = async (scenarioName) => {
  const res = await api.post(`/simulation/scenario/${scenarioName}`);
  return res.data;
};

// Model Evaluation APIs
export const fetchEvaluationMetrics = async () => {
  const res = await api.get("/evaluation");
  return res.data;
};

export const runModelEvaluation = async () => {
  const res = await api.post("/evaluation/run");
  return res.data;
};

// NOAA ASOS APIs
export const fetchNoaaStatus = async () => {
  const res = await api.get("/noaa/status");
  return res.data;
};

export const fetchNoaaStations = async () => {
  const res = await api.get("/noaa/stations");
  return res.data;
};

export default api;


