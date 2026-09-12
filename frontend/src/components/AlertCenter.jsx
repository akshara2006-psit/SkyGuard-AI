import React from "react";
import { Bell, Check, AlertOctagon, AlertTriangle, Info } from "lucide-react";

export default function AlertCenter({ alerts = [], onAcknowledge }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title"><Bell size={18} /> Alert Operations Center</div>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>All alerts acknowledged. Node telemetry status nominal.</p>
      </div>
    );
  }

  const getSeverityIcon = (sev) => {
    switch (sev) {
      case "CRITICAL":
        return <AlertOctagon size={18} color="#ef4444" />;
      case "WARNING":
        return <AlertTriangle size={18} color="#f59e0b" />;
      default:
        return <Info size={18} color="#3b82f6" />;
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <Bell size={18} color="#f59e0b" /> Active Alerts ({alerts.length})
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "400px", overflowY: "auto" }}>
        {alerts.map((al) => {
          const time = new Date(al.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          const isAck = al.status === "ACKNOWLEDGED";

          return (
            <div
              key={al.id}
              style={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "0.85rem 1rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "1rem",
                opacity: isAck ? 0.6 : 1
              }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
                <div style={{ marginTop: "2px" }}>{getSeverityIcon(al.severity)}</div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontWeight: 700, fontSize: "0.88rem", color: "#ffffff" }}>
                      {al.title}
                    </span>
                    <span className="font-mono" style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>
                      {time}
                    </span>
                    <span className={`badge ${al.severity === "CRITICAL" ? "badge-anomaly" : "badge-warning"}`}>
                      {al.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                    {al.message}
                  </div>
                  {al.recommended_action && (
                    <div style={{ fontSize: "0.75rem", color: "#93c5fd", marginTop: "0.25rem" }}>
                      <strong>Action:</strong> {al.recommended_action}
                    </div>
                  )}
                </div>
              </div>

              <div>
                {!isAck ? (
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={() => onAcknowledge(al.id)}
                    style={{ whiteSpace: "nowrap" }}
                  >
                    <Check size={14} /> Acknowledge
                  </button>
                ) : (
                  <span style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontStyle: "italic" }}>
                    Acknowledged
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
