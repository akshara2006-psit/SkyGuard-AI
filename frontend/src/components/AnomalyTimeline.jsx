import React from "react";
import { AlertCircle, Clock, CheckCircle } from "lucide-react";

export default function AnomalyTimeline({ anomalies = [] }) {
  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title"><Clock size={18} /> Anomaly Incident Timeline</div>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No anomalies recorded yet. Run simulation or inject faults to see events.</p>
      </div>
    );
  }

  const getBadgeStyle = (classification) => {
    switch (classification) {
      case "PROBABLE_SENSOR_ANOMALY":
      case "PROBABLE_SENSOR_FAULT":
        return "badge-anomaly";
      case "POSSIBLE_GENUINE_WEATHER_EVENT":
      case "POSSIBLE_WEATHER_EVENT":
        return "badge-event";
      case "POSSIBLE_COMMUNICATION_FAILURE":
      case "POSSIBLE_DATA_QUALITY_ISSUE":
        return "badge-warning";
      default:
        return "badge-healthy";
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <Clock size={18} color="#3b82f6" /> Anomaly Incident Timeline ({anomalies.length})
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "400px", overflowY: "auto" }}>
        {anomalies.map((a, idx) => {
          const time = new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          const isAnomaly = a.is_anomaly;

          return (
            <div
              key={a.id || idx}
              style={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "0.75rem 1rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "1rem"
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <span className="font-mono" style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>{time}</span>
                <span style={{ fontWeight: 700, fontSize: "0.85rem", color: "#ffffff" }}>{a.station_id}</span>
                <span className={`badge ${getBadgeStyle(a.classification)}`}>
                  {a.classification?.replace(/_/g, " ")}
                </span>
                {a.affected_sensor && (
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    ({a.affected_sensor} sensor)
                  </span>
                )}
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "1rem", fontSize: "0.78rem" }}>
                <div>
                  <span style={{ color: "var(--text-dim)" }}>Score: </span>
                  <span className="font-mono" style={{ fontWeight: 600, color: a.anomaly_score_pct > 50 ? "#ef4444" : "#10b981" }}>
                    {a.anomaly_score_pct}%
                  </span>
                </div>
                <div>
                  <span style={{ color: "var(--text-dim)" }}>Confidence: </span>
                  <span className="font-mono" style={{ fontWeight: 600, color: "#3b82f6" }}>
                    {a.confidence_pct}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
