import React, { useState, useEffect } from "react";
import { Activity, Cpu, CheckCircle2, Zap, HardDrive, ShieldAlert, BarChart3, Clock, AlertTriangle, RefreshCw, Play } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from "recharts";
import { fetchEvaluationMetrics, runModelEvaluation } from "../services/api";

export default function AnalyticsView({ onOpenBenchmark }) {
  const [evalData, setEvalData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchEvaluationMetrics();
      if (data && data.status === "completed") {
        setEvalData(data);
      } else if (data && data.error_message) {
        setError(data.error_message);
      } else {
        setError("Evaluation dataset unavailable or insufficient labelled data");
      }
    } catch (err) {
      console.error("Evaluation load error:", err);
      setError("Evaluation dataset unavailable or backend unreachable");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const handleRunLiveEvaluation = async () => {
    try {
      setRunning(true);
      setError(null);
      const res = await runModelEvaluation();
      if (res && res.status === "completed") {
        setEvalData(res);
      } else if (res && res.error_message) {
        setError(res.error_message);
      } else {
        setError("Evaluation failed to return valid metrics");
      }
    } catch (err) {
      console.error("Run evaluation error:", err);
      setError("Evaluation run failed: " + (err.message || "Backend error"));
    } finally {
      setRunning(false);
    }
  };

  const metrics = evalData?.metrics || null;
  const faultBreakdown = evalData?.fault_type_breakdown ? Object.values(evalData.fault_type_breakdown) : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Analytics Top Banner */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h2 className="card-title">
              <Activity size={20} color="#3b82f6" /> System Analytics & Dynamic Model Evaluation
            </h2>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
              Empirical verification executed directly against ground-truth labelled AWS datasets.
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <button
              className="btn btn-primary"
              onClick={handleRunLiveEvaluation}
              disabled={running}
            >
              {running ? (
                <>
                  <RefreshCw size={16} className="spin" /> Running Evaluation...
                </>
              ) : (
                <>
                  <Play size={16} /> Run Live Evaluation
                </>
              )}
            </button>
            <button className="btn btn-outline" onClick={onOpenBenchmark}>
              <BarChart3 size={16} /> Detailed Benchmark Report
            </button>
          </div>
        </div>

        {/* Evaluation Metadata Header */}
        <div style={{ display: "flex", gap: "1.5rem", marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border-subtle)", fontSize: "0.78rem", color: "var(--text-muted)" }}>
          <div>
            Status: <strong style={{ color: evalData ? "#10b981" : "#f59e0b" }}>{evalData ? "Completed" : (loading ? "Loading..." : "Not Evaluated")}</strong>
          </div>
          <div>
            Dataset: <strong>{evalData?.dataset || "benchmark_dataset_with_ground_truth.csv"}</strong>
          </div>
          <div>
            Samples Evaluated: <strong>{evalData?.evaluated_samples ? evalData.evaluated_samples.toLocaleString() : "N/A"}</strong>
          </div>
          {evalData?.evaluation_timestamp && (
            <div>
              Last Evaluated: <strong>{new Date(evalData.evaluation_timestamp).toLocaleTimeString()} ({new Date(evalData.evaluation_timestamp).toLocaleDateString()})</strong>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="card" style={{ background: "rgba(239, 68, 68, 0.12)", borderColor: "rgba(239, 68, 68, 0.3)", color: "#fca5a5" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", fontWeight: 600 }}>
            <AlertTriangle size={18} color="#ef4444" /> {error}
          </div>
        </div>
      )}

      {/* Model Performance Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
        <div className="card">
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Precision
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: metrics ? "#10b981" : "var(--text-dim)", marginTop: "0.25rem" }}>
            {metrics ? `${metrics.precision.toFixed(1)}%` : "Not benchmarked"}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Low False Alarm Rate
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Recall (Sensitivity)
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: metrics ? "#3b82f6" : "var(--text-dim)", marginTop: "0.25rem" }}>
            {metrics ? `${metrics.recall.toFixed(1)}%` : "Not benchmarked"}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            High Fault Capture Rate
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
            F1-Score
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: metrics ? "#8b5cf6" : "var(--text-dim)", marginTop: "0.25rem" }}>
            {metrics ? `${metrics.f1_score.toFixed(1)}%` : "Not benchmarked"}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Harmonic Mean Score
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
            False Positive Rate
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: metrics ? "#f59e0b" : "var(--text-dim)", marginTop: "0.25rem" }}>
            {metrics ? `${metrics.false_positive_rate.toFixed(1)}%` : "Not benchmarked"}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Minimal False Alarms
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Detection Latency
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: evalData ? "#06b6d4" : "var(--text-dim)", marginTop: "0.25rem" }}>
            {evalData?.avg_detection_latency_ms !== undefined ? `${evalData.avg_detection_latency_ms} ms` : "Not benchmarked"}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Measured per-sample latency
          </div>
        </div>
      </div>

      {/* Per-Fault Performance Breakdown */}
      {faultBreakdown.length > 0 && (
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: "1rem" }}>
            Calculated Per-Fault Category Detection Metrics
          </h3>
          <div style={{ height: "240px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={faultBreakdown} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis dataKey="fault_category" stroke="var(--text-muted)" fontSize={11} />
                <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={12} unit="%" />
                <Tooltip
                  contentStyle={{ background: "var(--bg-secondary)", borderColor: "var(--border-color)", borderRadius: "8px" }}
                />
                <Bar dataKey="detection_rate_pct" name="Detection Rate (%)" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="precision_pct" name="Precision (%)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="f1_score_pct" name="F1-Score (%)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Target Edge Profile & Hardware Section */}
      <div className="card" style={{ borderLeft: "4px solid #06b6d4" }}>
        <h3 className="card-title" style={{ marginBottom: "0.75rem" }}>
          <Cpu size={20} color="#06b6d4" /> Target Edge Deployment Profile (ESP32 Low-Power Screening)
        </h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
          Target hardware deployment specification for low-power anomaly screening on remote weather station nodes.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
          <div style={{ background: "var(--bg-secondary)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Target Hardware</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginTop: "0.2rem" }}>ESP32-S3 / ARM Cortex-M4</div>
            <div style={{ fontSize: "0.75rem", color: "#10b981", marginTop: "0.4rem" }}>Low Power (80mA operating)</div>
          </div>

          <div style={{ background: "var(--bg-secondary)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Target Edge Latency</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginTop: "0.2rem" }}>Target &lt; 5.0 ms</div>
            <div style={{ fontSize: "0.75rem", color: "#10b981", marginTop: "0.4rem" }}>On-chip screening target</div>
          </div>

          <div style={{ background: "var(--bg-secondary)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Quantized Model RAM</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginTop: "0.2rem" }}>Target ~48 KB SRAM</div>
            <div style={{ fontSize: "0.75rem", color: "#10b981", marginTop: "0.4rem" }}>Fits internal micro-RAM</div>
          </div>

          <div style={{ background: "var(--bg-secondary)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Deployment Model</div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff", marginTop: "0.2rem" }}>Hybrid Screening</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>Local screening → Central platform</div>
          </div>
        </div>
      </div>
    </div>
  );
}
