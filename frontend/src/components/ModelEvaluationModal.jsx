import React, { useState, useEffect } from "react";
import { X, CheckCircle, Target, BarChart, ShieldCheck, Activity, RefreshCw, Play, AlertTriangle } from "lucide-react";
import { fetchEvaluationMetrics, runModelEvaluation } from "../services/api";

export default function ModelEvaluationModal({ isOpen, onClose }) {
  const [evalData, setEvalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    fetchEvaluationMetrics()
      .then((data) => {
        if (data && data.status === "completed") {
          setEvalData(data);
        } else if (data && data.error_message) {
          setError(data.error_message);
        } else {
          setError("Evaluation dataset unavailable or insufficient labelled data");
        }
      })
      .catch((err) => {
        console.error("Modal metrics fetch error:", err);
        setError("Evaluation dataset unavailable or backend offline");
      })
      .finally(() => setLoading(false));
  }, [isOpen]);

  const handleRunLiveBenchmark = async () => {
    try {
      setRunning(true);
      setError(null);
      const res = await runModelEvaluation();
      if (res && res.status === "completed") {
        setEvalData(res);
      } else if (res && res.error_message) {
        setError(res.error_message);
      } else {
        setError("Evaluation run failed");
      }
    } catch (err) {
      console.error("Run live benchmark error:", err);
      setError("Evaluation run failed: " + (err.message || "Backend error"));
    } finally {
      setRunning(false);
    }
  };

  if (!isOpen) return null;

  const metrics = evalData?.metrics || null;
  const faultBreakdown = evalData?.fault_type_breakdown ? Object.values(evalData.fault_type_breakdown) : [];

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        background: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "1rem"
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{
          maxWidth: "850px",
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-color)",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="card-header">
          <div className="card-title">
            <ShieldCheck size={20} color="#10b981" /> Dynamic AI/ML Pipeline Evaluation & Benchmark Report
          </div>
          <button className="btn btn-outline btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: 0 }}>
            Empirical verification calculated directly from ground-truth labelled AWS telemetry predictions.
          </p>
          <button
            className="btn btn-primary btn-sm"
            onClick={handleRunLiveBenchmark}
            disabled={running}
          >
            {running ? (
              <>
                <RefreshCw size={14} className="spin" /> Executing Benchmark...
              </>
            ) : (
              <>
                <Play size={14} /> Run Live Benchmark
              </>
            )}
          </button>
        </div>

        {/* Dataset metadata banner */}
        {evalData && (
          <div style={{ background: "var(--bg-card)", padding: "0.6rem 0.85rem", borderRadius: "6px", marginBottom: "1.25rem", border: "1px solid var(--border-subtle)", fontSize: "0.75rem", display: "flex", gap: "1.25rem", color: "var(--text-muted)" }}>
            <div>Dataset: <strong style={{ color: "#ffffff" }}>{evalData.dataset}</strong></div>
            <div>Samples Evaluated: <strong style={{ color: "#ffffff" }}>{evalData.evaluated_samples?.toLocaleString()}</strong></div>
            <div>Anomalies Injected: <strong style={{ color: "#ffffff" }}>{evalData.total_anomalies_injected}</strong></div>
            <div>Inference Latency: <strong style={{ color: "#06b6d4" }}>{evalData.avg_detection_latency_ms} ms / reading</strong></div>
          </div>
        )}

        {error && (
          <div style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid #ef4444", borderRadius: "6px", padding: "0.75rem", color: "#fca5a5", fontSize: "0.8rem", marginBottom: "1.25rem" }}>
            <AlertTriangle size={16} inline color="#ef4444" /> {error}
          </div>
        )}

        {/* Metric Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.85rem", marginBottom: "1.5rem" }}>
          <div style={{ background: "var(--bg-card)", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase" }}>Recall (Sensitivity)</div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: metrics ? "#10b981" : "var(--text-dim)" }}>
              {metrics ? `${metrics.recall.toFixed(1)}%` : "N/A"}
            </div>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Faults Caught</div>
          </div>

          <div style={{ background: "var(--bg-card)", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase" }}>Precision</div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: metrics ? "#3b82f6" : "var(--text-dim)" }}>
              {metrics ? `${metrics.precision.toFixed(1)}%` : "N/A"}
            </div>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>True Anomaly Ratio</div>
          </div>

          <div style={{ background: "var(--bg-card)", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase" }}>F1-Score</div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: metrics ? "#8b5cf6" : "var(--text-dim)" }}>
              {metrics ? `${metrics.f1_score.toFixed(1)}%` : "N/A"}
            </div>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>Harmonic Mean</div>
          </div>

          <div style={{ background: "var(--bg-card)", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", textAlign: "center" }}>
            <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", textTransform: "uppercase" }}>False Positive Rate</div>
            <div style={{ fontSize: "1.6rem", fontWeight: 800, color: metrics ? "#f59e0b" : "var(--text-dim)" }}>
              {metrics ? `${metrics.false_positive_rate.toFixed(1)}%` : "N/A"}
            </div>
            <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>False Alarm Rate</div>
          </div>
        </div>

        {/* Fault Breakdown Table */}
        {faultBreakdown.length > 0 && (
          <>
            <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#ffffff", marginBottom: "0.5rem" }}>
              Per-Fault Type Calculated Performance
            </div>

            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left", marginBottom: "1.25rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-dim)" }}>
                  <th style={{ padding: "0.5rem 0.5rem" }}>Fault Category</th>
                  <th style={{ padding: "0.5rem 0.5rem" }}>Detected / Injected</th>
                  <th style={{ padding: "0.5rem 0.5rem" }}>Detection Rate</th>
                  <th style={{ padding: "0.5rem 0.5rem" }}>Precision</th>
                  <th style={{ padding: "0.5rem 0.5rem" }}>F1-Score</th>
                </tr>
              </thead>
              <tbody>
                {faultBreakdown.map((row, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "0.6rem 0.5rem", fontWeight: 600, color: "#e5e7eb" }}>{row.fault_category}</td>
                    <td style={{ padding: "0.6rem 0.5rem" }} className="font-mono">{row.detected} / {row.total_injected}</td>
                    <td style={{ padding: "0.6rem 0.5rem" }}>
                      <span className="badge badge-healthy font-mono">{row.detection_rate_pct}%</span>
                    </td>
                    <td style={{ padding: "0.6rem 0.5rem" }} className="font-mono">{row.precision_pct}%</td>
                    <td style={{ padding: "0.6rem 0.5rem" }} className="font-mono">{row.f1_score_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button className="btn btn-outline" onClick={onClose}>
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
}
