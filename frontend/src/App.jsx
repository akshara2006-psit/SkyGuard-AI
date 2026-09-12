import React, { useState, useEffect, useCallback } from "react";
import Navbar from "./components/Navbar";
import SummaryCards from "./components/SummaryCards";
import StationList from "./components/StationList";
import StationDetail from "./components/StationDetail";
import AnomalyTimeline from "./components/AnomalyTimeline";
import AlertCenter from "./components/AlertCenter";
import SimulationControls from "./components/SimulationControls";
import ModelEvaluationModal from "./components/ModelEvaluationModal";
import AnalyticsView from "./components/AnalyticsView";
import AboutView from "./components/AboutView";
import LoginPage from "./components/LoginPage";

import {
  fetchSummary,
  fetchStations,
  fetchStationDetail,
  fetchReadings,
  fetchAnomalies,
  fetchStationHealth,
  fetchAlerts,
  acknowledgeAlert,
  fetchSimulationStatus,
  startSimulation,
  stopSimulation,
  injectSimulationFault,
  triggerScenario,
} from "./services/api";

import { Radio, Activity, Bell, Clock, ShieldCheck, CheckCircle2 } from "lucide-react";

export default function App() {
  // Authentication State
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("skyguard_user");
    return saved ? JSON.parse(saved) : null;
  });

  const [summary, setSummary] = useState(null);
  const [stations, setStations] = useState([]);
  const [selectedStationId, setSelectedStationId] = useState("AWS-001");
  const [stationDetail, setStationDetail] = useState(null);
  const [readings, setReadings] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [allAnomalies, setAllAnomalies] = useState([]);
  const [health, setHealth] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [simRunning, setSimRunning] = useState(false);
  const [activeTab, setActiveTab] = useState("overview"); // overview | stations | alerts | analytics | simulation | about
  const [isEvalModalOpen, setIsEvalModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem("skyguard_user", JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("skyguard_user");
  };

  // Load all dashboard state
  const loadDashboardData = useCallback(async () => {
    try {
      setError(null);
      const [sumData, stList, alList, simStat] = await Promise.all([
        fetchSummary().catch(() => null),
        fetchStations().catch(() => []),
        fetchAlerts().catch(() => []),
        fetchSimulationStatus().catch(() => ({ running: false })),
      ]);

      if (sumData) setSummary(sumData);
      if (stList && stList.length > 0) setStations(stList);
      if (alList) setAlerts(alList);
      if (simStat) setSimRunning(simStat.running);
    } catch (err) {
      console.error("Dashboard refresh error:", err);
      setError("Unable to connect to SkyGuard AI backend (http://localhost:8000). Ensure the backend is running.");
    }
  }, []);

  // Load selected station data
  const loadStationData = useCallback(async (id) => {
    if (!id) return;
    try {
      const [detail, reads, anoms, hlth, allAnom] = await Promise.all([
        fetchStationDetail(id).catch(() => null),
        fetchReadings(id, 40).catch(() => []),
        fetchAnomalies(id, 20).catch(() => []),
        fetchStationHealth(id).catch(() => []),
        fetchAnomalies(null, 50).catch(() => []),
      ]);

      if (detail) setStationDetail(detail);
      if (reads) setReadings(reads);
      if (anoms) setAnomalies(anoms);
      if (hlth) setHealth(hlth);
      if (allAnom) setAllAnomalies(allAnom);
    } catch (err) {
      console.error("Station data error:", err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    if (user) {
      loadDashboardData();
    }
  }, [user, loadDashboardData]);

  // Load selected station
  useEffect(() => {
    if (user && selectedStationId) {
      loadStationData(selectedStationId);
    }
  }, [user, selectedStationId, loadStationData]);

  // Polling loop when simulation is running
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      loadDashboardData();
      if (selectedStationId) {
        loadStationData(selectedStationId);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [user, loadDashboardData, loadStationData, selectedStationId]);

  // Handlers
  const handleToggleSimulation = async () => {
    try {
      if (simRunning) {
        await stopSimulation();
        setSimRunning(false);
      } else {
        await startSimulation();
        setSimRunning(true);
      }
      loadDashboardData();
    } catch (err) {
      console.error("Toggle simulation error:", err);
    }
  };

  const handleTriggerScenario = async (scId) => {
    try {
      await triggerScenario(scId);
      setSimRunning(true);
      setTimeout(() => {
        loadDashboardData();
        if (selectedStationId) loadStationData(selectedStationId);
      }, 500);
    } catch (err) {
      console.error("Trigger scenario error:", err);
    }
  };

  const handleInjectFault = async (stId, fType, dur) => {
    try {
      await injectSimulationFault(stId, fType, dur);
      if (!simRunning) {
        await startSimulation();
        setSimRunning(true);
      }
      setTimeout(() => {
        loadDashboardData();
        if (selectedStationId) loadStationData(selectedStationId);
      }, 500);
    } catch (err) {
      console.error("Inject fault error:", err);
    }
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      const updated = await fetchAlerts();
      setAlerts(updated);
    } catch (err) {
      console.error("Acknowledge alert error:", err);
    }
  };

  if (!user) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app-container">
      <Navbar
        simRunning={simRunning}
        onToggleSimulation={handleToggleSimulation}
        onOpenEvalModal={() => setIsEvalModalOpen(true)}
        onRefresh={() => {
          loadDashboardData();
          if (selectedStationId) loadStationData(selectedStationId);
        }}
        loading={loading}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        user={user}
        onLogout={handleLogout}
      />

      <main className="main-content">
        {error && (
          <div style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid #ef4444", borderRadius: "8px", padding: "0.85rem 1.25rem", color: "#fca5a5", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
            <strong>Connection Warning:</strong> {error}
          </div>
        )}

        {/* Global Summary Bar always visible on top */}
        <SummaryCards summary={summary} />

        {/* TAB 1: OVERVIEW */}
        {activeTab === "overview" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div className="dashboard-layout">
              {/* Station List */}
              <StationList
                stations={stations}
                selectedId={selectedStationId}
                onSelectStation={(id) => {
                  setSelectedStationId(id);
                  setActiveTab("stations");
                }}
              />

              {/* Recent Alerts & System Health Summary */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                <div className="card">
                  <div className="card-header">
                    <div className="card-title">
                      <Bell size={18} color="#8b5cf6" /> Recent Anomaly Alerts
                    </div>
                  </div>
                  <AlertCenter alerts={alerts.slice(0, 5)} onAcknowledge={handleAcknowledgeAlert} />
                </div>

                <div className="card">
                  <div className="card-header">
                    <div className="card-title">
                      <Clock size={18} color="#3b82f6" /> Recent Network Incidents
                    </div>
                  </div>
                  <AnomalyTimeline anomalies={allAnomalies.slice(0, 5)} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: STATIONS */}
        {activeTab === "stations" && (
          <div className="dashboard-layout">
            <StationList
              stations={stations}
              selectedId={selectedStationId}
              onSelectStation={(id) => setSelectedStationId(id)}
            />
            <StationDetail
              station={stationDetail}
              readings={readings}
              anomalies={anomalies}
              health={health}
            />
          </div>
        )}

        {/* TAB 3: ALERTS */}
        {activeTab === "alerts" && (
          <AlertCenter alerts={alerts} onAcknowledge={handleAcknowledgeAlert} />
        )}

        {/* TAB 4: ANALYTICS */}
        {activeTab === "analytics" && (
          <AnalyticsView onOpenBenchmark={() => setIsEvalModalOpen(true)} />
        )}

        {/* TAB 5: SIMULATION */}
        {activeTab === "simulation" && (
          <SimulationControls
            stations={stations}
            onTriggerScenario={handleTriggerScenario}
            onInjectFault={handleInjectFault}
          />
        )}

        {/* TAB 6: ABOUT */}
        {activeTab === "about" && <AboutView />}
      </main>

      {/* Model Benchmark Modal */}
      <ModelEvaluationModal
        isOpen={isEvalModalOpen}
        onClose={() => setIsEvalModalOpen(false)}
      />
    </div>
  );
}
