import React from "react";
import { Thermometer, Gauge, Droplets, MapPin } from "lucide-react";

export default function StationList({ stations, selectedId, onSelectStation }) {
  const getBadgeClass = (status) => {
    switch (status) {
      case "HEALTHY":
        return "badge-healthy";
      case "WARNING":
        return "badge-warning";
      case "DEGRADED":
      case "CRITICAL":
      case "ANOMALY":
        return "badge-anomaly";
      default:
        return "badge-healthy";
    }
  };

  return (
    <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div className="card-header">
        <div className="card-title">
          <MapPin size={18} color="#3b82f6" /> AWS Network ({stations.length})
        </div>
      </div>

      <div style={{ overflowY: "auto", flex: 1, paddingRight: "0.25rem" }}>
        {stations.map((s) => {
          const isSelected = s.id === selectedId;
          const status = s.health_status || "HEALTHY";
          const temp = s.last_temperature != null ? `${s.last_temperature.toFixed(1)}°C` : "--";
          const pres = s.last_pressure != null ? `${s.last_pressure.toFixed(0)} hPa` : "--";
          const hum = s.last_humidity != null ? `${s.last_humidity.toFixed(0)}%` : "--";

          return (
            <div
              key={s.id}
              className={`station-item ${isSelected ? "active" : ""}`}
              onClick={() => onSelectStation(s.id)}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                  <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "#ffffff" }}>
                    {s.id}
                  </span>
                  {s.source === "NOAA_ASOS" ? (
                    <span style={{ fontSize: "0.62rem", padding: "1px 5px", borderRadius: "3px", background: "rgba(59, 130, 246, 0.2)", color: "#60a5fa", border: "1px solid rgba(59, 130, 246, 0.4)", fontWeight: 600 }}>
                      NOAA
                    </span>
                  ) : (
                    <span style={{ fontSize: "0.62rem", padding: "1px 5px", borderRadius: "3px", background: "rgba(107, 114, 128, 0.2)", color: "#9ca3af", border: "1px solid rgba(107, 114, 128, 0.4)" }}>
                      SIM
                    </span>
                  )}
                </div>
                <span className={`badge ${getBadgeClass(status)}`}>
                  {status}
                </span>
              </div>

              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                {s.name}
              </div>

              <div style={{ display: "flex", gap: "0.85rem", fontSize: "0.75rem", color: "var(--text-main)" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <Thermometer size={13} color="#f87171" /> {temp}
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <Gauge size={13} color="#60a5fa" /> {pres}
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                  <Droplets size={13} color="#34d399" /> {hum}
                </span>
              </div>

              {s.health_score != null && (
                <div style={{ marginTop: "0.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.68rem", color: "var(--text-dim)", marginBottom: "0.2rem" }}>
                    <span>Health Index</span>
                    <span style={{ fontWeight: 600, color: s.health_score > 70 ? "#10b981" : "#ef4444" }}>
                      {s.health_score.toFixed(0)}%
                    </span>
                  </div>
                  <div style={{ width: "100%", height: "4px", background: "var(--border-subtle)", borderRadius: "2px", overflow: "hidden" }}>
                    <div
                      style={{
                        width: `${s.health_score}%`,
                        height: "100%",
                        background: s.health_score > 70 ? "#10b981" : s.health_score > 50 ? "#f59e0b" : "#ef4444",
                        transition: "width 0.3s ease"
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
