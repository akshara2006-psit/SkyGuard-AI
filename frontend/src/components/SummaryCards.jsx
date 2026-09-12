import React from "react";
import { Radio, CheckCircle, AlertTriangle, AlertOctagon, Bell } from "lucide-react";

export default function SummaryCards({ summary }) {
  const {
    total_stations = 0,
    healthy = 0,
    warning = 0,
    active_anomalies = 0,
    recent_anomalies_24h = 0,
    open_alerts = 0
  } = summary || {};

  const anomalyCount = active_anomalies ?? recent_anomalies_24h ?? 0;

  const cards = [
    {
      label: "Total AWS Stations",
      value: total_stations,
      icon: <Radio size={22} color="#3b82f6" />,
      bg: "rgba(59, 130, 246, 0.12)",
    },
    {
      label: "Healthy Stations",
      value: healthy,
      icon: <CheckCircle size={22} color="#10b981" />,
      bg: "rgba(16, 185, 129, 0.12)",
    },
    {
      label: "Warning State",
      value: warning,
      icon: <AlertTriangle size={22} color="#f59e0b" />,
      bg: "rgba(245, 158, 11, 0.12)",
    },
    {
      label: "Active Anomalies",
      value: anomalyCount,
      icon: <AlertOctagon size={22} color="#ef4444" />,
      bg: "rgba(239, 68, 68, 0.12)",
    },
    {
      label: "Open Alerts",
      value: open_alerts,
      icon: <Bell size={22} color="#8b5cf6" />,
      bg: "rgba(139, 92, 246, 0.12)",
    },
  ];

  return (
    <div className="summary-grid">
      {cards.map((c, i) => (
        <div key={i} className="summary-card">
          <div className="icon-box" style={{ background: c.bg }}>
            {c.icon}
          </div>
          <div>
            <div className="value">{c.value}</div>
            <div className="label">{c.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
