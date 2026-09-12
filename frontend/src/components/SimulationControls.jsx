import React, { useState } from "react";
import { Zap, Play, RotateCcw, AlertTriangle, CloudRain, Flame, Snowflake, TrendingUp, WifiOff } from "lucide-react";

export default function SimulationControls({
  stations = [],
  onTriggerScenario,
  onInjectFault
}) {
  const [selectedStation, setSelectedStation] = useState("AWS-001");
  const [selectedFault, setSelectedFault] = useState("temperature_spike");
  const [duration, setDuration] = useState(8);
  const [activeScenario, setActiveScenario] = useState("normal");

  const scenarios = [
    { id: "normal", label: "Reset Normal", icon: <RotateCcw size={14} />, desc: "Nominal weather across all stations" },
    { id: "temperature_spike", label: "Temp Spike (AWS-001)", icon: <Flame size={14} color="#f87171" />, desc: "Abrupt +25°C jump on Safdarjung" },
    { id: "frozen_humidity", label: "Frozen Sensor (AWS-002)", icon: <Snowflake size={14} color="#60a5fa" />, desc: "Stuck sensor values on Colaba" },
    { id: "sensor_drift", label: "Sensor Drift (AWS-003)", icon: <TrendingUp size={14} color="#f59e0b" />, desc: "Gradual deviation over time on Nungambakkam" },
    { id: "comm_failure", label: "Comm Failure (AWS-004)", icon: <WifiOff size={14} color="#ef4444" />, desc: "Missing telemetry packet loss on Kolkata" },
    { id: "weather_event", label: "Genuine Weather Event (AWS-005)", icon: <CloudRain size={14} color="#06b6d4" />, desc: "Coherent multi-parameter change across Bengaluru" },
    { id: "multivariate_inconsistency", label: "Multivariate Inconsistency (AWS-006)", icon: <AlertTriangle size={14} color="#eab308" />, desc: "Inconsistent multi-parameter behaviour on Begumpet" },
  ];

  const handleScenarioClick = (scId) => {
    setActiveScenario(scId);
    onTriggerScenario(scId);
  };

  const handleCustomInject = (e) => {
    e.preventDefault();
    onInjectFault(selectedStation, selectedFault, parseInt(duration));
  };

  return (
    <div className="card" style={{ marginBottom: "1.5rem" }}>
      <div className="card-header">
        <div className="card-title">
          <Zap size={18} color="#eab308" /> SIMULATION LAB
        </div>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Controlled scenarios for evaluating real-time anomaly detection and sensor diagnostics.
        </span>
      </div>

      {/* Preset Scenarios */}
      <div style={{ marginBottom: "1rem" }}>
        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
          Predefined Simulation Scenarios
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "0.6rem" }}>
          {scenarios.map((sc) => (
            <button
              key={sc.id}
              className={`btn btn-outline ${activeScenario === sc.id ? "btn-primary" : ""}`}
              onClick={() => handleScenarioClick(sc.id)}
              style={{ justifyContent: "flex-start", padding: "0.6rem 0.85rem", height: "auto" }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem", textAlign: "left" }}>
                <span style={{ marginTop: "2px" }}>{sc.icon}</span>
                <div>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700 }}>{sc.label}</div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 400 }}>{sc.desc}</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Custom Inject */}
      <form onSubmit={handleCustomInject} style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center", background: "var(--bg-secondary)", padding: "0.75rem 1rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem" }}>
          <span style={{ color: "var(--text-dim)" }}>Target AWS:</span>
          <select
            value={selectedStation}
            onChange={(e) => setSelectedStation(e.target.value)}
            style={{ background: "var(--bg-card)", color: "#ffffff", border: "1px solid var(--border-color)", padding: "0.3rem 0.6rem", borderRadius: "4px", fontSize: "0.8rem" }}
          >
            {stations.map((s) => (
              <option key={s.id} value={s.id}>{s.id} ({s.name})</option>
            ))}
          </select>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem" }}>
          <span style={{ color: "var(--text-dim)" }}>Fault Type:</span>
          <select
            value={selectedFault}
            onChange={(e) => setSelectedFault(e.target.value)}
            style={{ background: "var(--bg-card)", color: "#ffffff", border: "1px solid var(--border-color)", padding: "0.3rem 0.6rem", borderRadius: "4px", fontSize: "0.8rem" }}
          >
            <option value="temperature_spike">Temperature Spike (+30°C)</option>
            <option value="pressure_spike">Pressure Spike (+40 hPa)</option>
            <option value="humidity_spike">Humidity Spike</option>
            <option value="frozen_sensor">Frozen Sensor (Stuck reading)</option>
            <option value="drift">Sensor Drift (Slope degradation)</option>
            <option value="communication_failure">Communication Failure (Drop packet)</option>
            <option value="weather_event">Genuine Weather Event (Coherent change)</option>
            <option value="multivariate_inconsistency">Multivariate Inconsistency (Inconsistent parameters)</option>
          </select>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem" }}>
          <span style={{ color: "var(--text-dim)" }}>Steps:</span>
          <input
            type="number"
            min={1}
            max={30}
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            style={{ width: "60px", background: "var(--bg-card)", color: "#ffffff", border: "1px solid var(--border-color)", padding: "0.3rem 0.6rem", borderRadius: "4px", fontSize: "0.8rem" }}
          />
        </div>

        <button type="submit" className="btn btn-primary btn-sm">
          <Play size={12} /> Inject Fault
        </button>
      </form>
    </div>
  );
}
