import React from "react";
import {
  ShieldCheck,
  Play,
  Square,
  RefreshCw,
  BarChart2,
  LogOut,
  LayoutDashboard,
  Radio,
  Bell,
  Activity,
  FlaskConical,
  Info
} from "lucide-react";

export default function Navbar({
  simRunning,
  onToggleSimulation,
  onOpenEvalModal,
  onRefresh,
  loading,
  activeTab,
  onTabChange,
  user,
  onLogout
}) {
  const navTabs = [
    { id: "overview", label: "Overview", icon: <LayoutDashboard size={16} /> },
    { id: "stations", label: "Stations", icon: <Radio size={16} /> },
    { id: "alerts", label: "Alerts", icon: <Bell size={16} /> },
    { id: "analytics", label: "Analytics", icon: <Activity size={16} /> },
    { id: "simulation", label: "Simulation", icon: <FlaskConical size={16} /> },
    { id: "about", label: "About", icon: <Info size={16} /> },
  ];

  return (
    <header className="navbar-container" style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border-color)", sticky: "top", zIndex: 50 }}>
      {/* Top Header Row */}
      <div className="navbar" style={{ padding: "0.75rem 2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div className="brand-group">
          <div className="brand-icon">
            <ShieldCheck size={24} />
          </div>
          <div>
            <div className="brand-title">
              SKYGUARD AI
              
            </div>
            <div className="brand-subtitle">
              Intelligent Real-Time Anomaly Detection for Automatic Weather Stations
            </div>
          </div>
        </div>

        <div className="nav-actions">
          <div className="sim-indicator">
            <div className={`dot ${simRunning ? "live" : "stopped"}`} />
            <span>{simRunning ? "LIVE SIMULATION ACTIVE" : "SIMULATION PAUSED"}</span>
          </div>

          <button
            className={`btn ${simRunning ? "btn-danger" : "btn-primary"}`}
            onClick={onToggleSimulation}
          >
            {simRunning ? (
              <>
                <Square size={14} /> Stop Simulation
              </>
            ) : (
              <>
                <Play size={14} /> Start Simulation
              </>
            )}
          </button>

          <button className="btn btn-outline" onClick={onOpenEvalModal}>
            <BarChart2 size={15} /> Model Benchmark
          </button>

          <button
            className="btn btn-outline"
            onClick={onRefresh}
            disabled={loading}
            title="Refresh Data"
          >
            <RefreshCw size={15} className={loading ? "spin" : ""} />
          </button>

          {/* User Profile & Logout */}
          {user && (
            <div className="user-profile">
              <div className="user-avatar" title={user.email}>
                {user.picture ? (
                  <img src={user.picture} alt={user.name} />
                ) : (
                  user.name.charAt(0).toUpperCase()
                )}
              </div>
              <span className="user-name">{user.name}</span>
              <button
                className="btn btn-outline btn-sm"
                onClick={onLogout}
                title="Logout"
                style={{ padding: "0.3rem 0.5rem" }}
              >
                <LogOut size={14} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="main-nav-bar" style={{ padding: "0 2rem", background: "var(--bg-primary)", borderTop: "1px solid var(--border-subtle)", display: "flex", gap: "0.25rem" }}>
        {navTabs.map((t) => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? "active" : ""}`}
            onClick={() => onTabChange(t.id)}
            style={{ padding: "0.65rem 1.1rem" }}
          >
            {t.icon}
            <span>{t.label}</span>
          </button>
        ))}
      </div>
    </header>
  );
}
