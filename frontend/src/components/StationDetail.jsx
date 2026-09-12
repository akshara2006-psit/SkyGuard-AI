import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import {
  Thermometer,
  Gauge,
  Droplets,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  TrendingUp,
  Cpu,
  Wrench,
} from "lucide-react";

export default function StationDetail({
  station,
  readings = [],
  anomalies = [],
  health = [],
}) {
  if (!station) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "4rem" }}>
        <p style={{ color: "var(--text-muted)" }}>Select an AWS node to inspect real-time telemetry.</p>
      </div>
    );
  }

  // Get latest anomaly record
  const latestAnomaly = anomalies.length > 0 ? anomalies[0] : null;
  const isAnomalous = latestAnomaly && latestAnomaly.is_anomaly;

  // Format charts data (last 30 readings in chronological order)
  const chartData = readings.slice(-35).map((r) => {
    const timeStr = r.timestamp ? new Date(r.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : "";
    return {
      time: timeStr,
      temp: r.temperature,
      pres: r.pressure,
      hum: r.humidity,
    };
  });

  const getStatusColor = (classification) => {
    switch (classification) {
      case "PROBABLE_SENSOR_ANOMALY":
      case "PROBABLE_SENSOR_FAULT":
        return "#ef4444";
      case "POSSIBLE_GENUINE_WEATHER_EVENT":
      case "POSSIBLE_WEATHER_EVENT":
        return "#06b6d4";
      case "POSSIBLE_COMMUNICATION_FAILURE":
        return "#f59e0b";
      case "POSSIBLE_DATA_QUALITY_ISSUE":
        return "#eab308";
      default:
        return "#10b981";
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* Header Info */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
              <h2 style={{ fontSize: "1.4rem", fontWeight: 800, color: "#ffffff" }}>
                {station.id} — {station.name}
              </h2>
              <span className={`badge ${station.health_status === "HEALTHY" ? "badge-healthy" : "badge-anomaly"}`}>
                {station.health_status || "HEALTHY"}
              </span>
              {station.source === "NOAA_ASOS" ? (
                <span style={{ fontSize: "0.72rem", padding: "2px 8px", borderRadius: "4px", background: "rgba(59, 130, 246, 0.2)", color: "#60a5fa", border: "1px solid rgba(59, 130, 246, 0.4)", fontWeight: 600 }}>
                  NOAA ASOS (Real Data)
                </span>
              ) : (
                <span style={{ fontSize: "0.72rem", padding: "2px 8px", borderRadius: "4px", background: "rgba(107, 114, 128, 0.2)", color: "#9ca3af", border: "1px solid rgba(107, 114, 128, 0.4)" }}>
                  Simulation Node
                </span>
              )}
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              Lat: {station.latitude?.toFixed(4)}°N | Lon: {station.longitude?.toFixed(4)}°E | Elevation: {station.elevation}m | {station.location_desc}
            </div>
          </div>

          <div style={{ display: "flex", gap: "1.5rem", background: "var(--bg-secondary)", padding: "0.75rem 1.25rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase" }}>Temperature</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#f87171" }}>
                {station.last_temperature != null ? `${station.last_temperature.toFixed(1)}°C` : "--"}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase" }}>Pressure</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#60a5fa" }}>
                {station.last_pressure != null ? `${station.last_pressure.toFixed(1)} hPa` : "--"}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase" }}>Humidity</div>
              <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#34d399" }}>
                {station.last_humidity != null ? `${station.last_humidity.toFixed(0)}%` : "--"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Diagnostic Banner */}
      {latestAnomaly && (
        <div
          className="card"
          style={{
            borderLeft: `4px solid ${getStatusColor(latestAnomaly.classification)}`,
            background: isAnomalous ? "rgba(239, 68, 68, 0.05)" : "var(--bg-card)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.85rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              {isAnomalous ? (
                <AlertCircle size={20} color={getStatusColor(latestAnomaly.classification)} />
              ) : (
                <CheckCircle size={20} color="#10b981" />
              )}
              <span style={{ fontWeight: 700, fontSize: "1.05rem", color: "#ffffff" }}>
                {latestAnomaly.classification?.replace(/_/g, " ")}
              </span>
              {latestAnomaly.affected_sensor && (
                <span className="badge badge-anomaly font-mono">
                  {latestAnomaly.affected_sensor.toUpperCase()} SENSOR
                </span>
              )}
            </div>

            <div style={{ display: "flex", gap: "1.25rem", alignItems: "center" }}>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: "0.4rem" }}>Anomaly Score:</span>
                <span className="font-mono" style={{ fontWeight: 700, color: latestAnomaly.anomaly_score_pct > 50 ? "#ef4444" : "#10b981" }}>
                  {latestAnomaly.anomaly_score_pct}%
                </span>
              </div>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginRight: "0.4rem" }}>Confidence:</span>
                <span className="font-mono" style={{ fontWeight: 700, color: "#3b82f6" }}>
                  {latestAnomaly.confidence_pct}%
                </span>
              </div>
            </div>
          </div>

          {/* AI Explanation Text */}
          <div style={{ fontSize: "0.88rem", color: "#e5e7eb", lineHeight: 1.6, marginBottom: "0.85rem" }}>
            {latestAnomaly.reason || "Sensor telemetry within baseline operating distribution."}
          </div>

          {/* Explainability Panel: Model Feature Attribution */}
          {latestAnomaly.feature_attribution && (
            <div style={{ background: "var(--bg-secondary)", padding: "0.75rem 1rem", borderRadius: "6px", border: "1px solid var(--border-subtle)", marginBottom: "0.85rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#60a5fa", marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.05em", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <Cpu size={14} /> Explainability: Model Feature Attribution
              </div>
              <div style={{ fontSize: "0.82rem", color: "var(--text-main)", marginBottom: "0.4rem" }}>
                {latestAnomaly.feature_attribution.explanation_summary || "Feature attribution derived from Isolation Forest decision tree splits."}
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontStyle: "italic" }}>
                Method: {latestAnomaly.feature_attribution.attribution_method || "Isolation Forest Decision Path Attribution"}
              </div>
            </div>
          )}

          {/* Spatial Consistency Panel */}
          {(() => {
            const sc = latestAnomaly.evidence?.spatial_consistency;
            let spatialStatus = "INSUFFICIENT EVIDENCE";
            let badgeClass = "badge-warning";
            if (sc) {
              if (sc.regional_pattern === "SUPPORTED" || (sc.neighbor_count > 0 && !sc.spatial_anomaly)) {
                spatialStatus = "SUPPORTED";
                badgeClass = "badge-healthy";
              } else if (sc.regional_pattern === "NOT_SUPPORTED" || sc.spatial_anomaly === true) {
                spatialStatus = "NOT SUPPORTED";
                badgeClass = "badge-anomaly";
              } else {
                spatialStatus = "INSUFFICIENT EVIDENCE";
                badgeClass = "badge-warning";
              }
            }
            return (
              <div style={{ background: "var(--bg-secondary)", padding: "0.75rem 1rem", borderRadius: "6px", border: "1px solid var(--border-subtle)", marginBottom: "0.85rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.3rem" }}>
                  <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    Spatial Consistency (Nearby AWS Cross-Check)
                  </div>
                  <span className={`badge ${badgeClass}`}>
                    {spatialStatus}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                  {sc?.description || "Spatial Evidence: Insufficient nearby AWS observations available for regional verification."}
                </div>
              </div>
            );
          })()}

          {/* Observed vs AI-Estimated Expected Values */}
          {latestAnomaly.expected_temperature != null && (
            <div style={{ background: "var(--bg-secondary)", padding: "0.75rem 1rem", borderRadius: "6px", border: "1px solid var(--border-subtle)", marginBottom: "0.85rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", marginBottom: "0.4rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Observed vs AI-Estimated Expected Value
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "0.75rem" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Temperature: </span>
                  <span className="font-mono" style={{ fontWeight: 700, color: "#f87171" }}>{latestAnomaly.observed_temperature?.toFixed(1) ?? "--"}°C</span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}> (Expected: {latestAnomaly.expected_temperature?.toFixed(1) ?? "--"}°C)</span>
                </div>
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Pressure: </span>
                  <span className="font-mono" style={{ fontWeight: 700, color: "#60a5fa" }}>{latestAnomaly.observed_pressure?.toFixed(1) ?? "--"} hPa</span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}> (Expected: {latestAnomaly.expected_pressure?.toFixed(1) ?? "--"})</span>
                </div>
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Humidity: </span>
                  <span className="font-mono" style={{ fontWeight: 700, color: "#34d399" }}>{latestAnomaly.observed_humidity?.toFixed(0) ?? "--"}%</span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}> (Expected: {latestAnomaly.expected_humidity?.toFixed(0) ?? "--"}%)</span>
                </div>
              </div>
            </div>
          )}

          {/* Recommended Action */}
          {latestAnomaly.recommended_action && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", fontSize: "0.82rem", color: "#93c5fd", background: "rgba(59, 130, 246, 0.1)", padding: "0.6rem 0.85rem", borderRadius: "6px", border: "1px solid rgba(59, 130, 246, 0.2)" }}>
              <Wrench size={16} />
              <span><strong>Recommended Action:</strong> {latestAnomaly.recommended_action}</span>
            </div>
          )}
        </div>
      )}

      {/* Sensor Graphs */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <TrendingUp size={18} color="#3b82f6" /> Live Sensor Telemetry (Time-Series)
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1.5rem" }}>
          {/* Temperature Chart */}
          <div>
            <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#f87171", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <Thermometer size={14} /> Temperature (°C)
            </div>
            <div style={{ height: 160, width: "100%" }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                  <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                  <YAxis stroke="#6b7280" fontSize={11} domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ backgroundColor: "#111827", borderColor: "#374151" }} />
                  <Line type="monotone" dataKey="temp" stroke="#f87171" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pressure Chart */}
          <div>
            <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#60a5fa", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <Gauge size={14} /> Barometric Pressure (hPa)
            </div>
            <div style={{ height: 160, width: "100%" }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                  <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                  <YAxis stroke="#6b7280" fontSize={11} domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ backgroundColor: "#111827", borderColor: "#374151" }} />
                  <Line type="monotone" dataKey="pres" stroke="#60a5fa" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Humidity Chart */}
          <div>
            <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#34d399", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <Droplets size={14} /> Relative Humidity (%)
            </div>
            <div style={{ height: 160, width: "100%" }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                  <XAxis dataKey="time" stroke="#6b7280" fontSize={11} />
                  <YAxis stroke="#6b7280" fontSize={11} domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: "#111827", borderColor: "#374151" }} />
                  <Line type="monotone" dataKey="hum" stroke="#34d399" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Sensor Health Engine Section */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Cpu size={18} color="#10b981" /> Sensor Health & Maintenance Intelligence
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}>
          {health.map((h, idx) => (
            <div key={idx} style={{ background: "var(--bg-secondary)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ fontWeight: 700, fontSize: "0.9rem", textTransform: "capitalize", color: "#ffffff" }}>
                  {h.sensor_type} Sensor
                </span>
                <span className={`badge ${h.status === "HEALTHY" ? "badge-healthy" : (h.status === "WARNING" ? "badge-warning" : "badge-anomaly")}`}>
                  {h.status}
                </span>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.4rem" }}>
                <div style={{ fontSize: "1.6rem", fontWeight: 800, color: h.health_score > 75 ? "#10b981" : (h.health_score > 50 ? "#f59e0b" : "#ef4444") }}>
                  {h.health_score?.toFixed(0)}%
                </div>
                <div style={{ fontSize: "0.72rem", fontWeight: 700, color: h.degradation_trend === "DECLINING" ? "#ef4444" : "#10b981" }}>
                  Trend: {h.degradation_trend || "STABLE"}
                </div>
              </div>

              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: "0.25rem", marginBottom: "0.75rem" }}>
                <div>Recent Anomalies: <strong style={{ color: "#ffffff" }}>{h.recent_anomaly_count}</strong></div>
                <div>Missing Data Rate: <strong style={{ color: "#ffffff" }}>{(h.missing_data_rate * 100).toFixed(1)}%</strong></div>
                <div>Consistency Score: <strong style={{ color: "#ffffff" }}>{(h.consistency_score * 100).toFixed(0)}%</strong></div>
              </div>

              {h.maintenance_recommendation && (
                <div style={{ background: "var(--bg-card)", padding: "0.5rem 0.65rem", borderRadius: "4px", fontSize: "0.72rem", borderLeft: "3px solid #3b82f6" }}>
                  <div style={{ fontWeight: 700, color: "#93c5fd", marginBottom: "0.1rem" }}>
                    Recommendation ({h.maintenance_status?.replace(/_/g, " ")})
                  </div>
                  <div style={{ color: "var(--text-main)", lineHeight: 1.3 }}>
                    {h.maintenance_recommendation}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
