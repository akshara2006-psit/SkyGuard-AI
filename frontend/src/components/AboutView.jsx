import React from "react";
import { ShieldCheck, Target, Award, Cpu, BookOpen, Layers, CheckCircle2, HeartPulse, Sparkles } from "lucide-react";

export default function AboutView() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Product Mission Hero */}
      <div className="card" style={{ background: "linear-gradient(135deg, var(--bg-card) 0%, rgba(37, 99, 235, 0.1) 100%)", borderColor: "rgba(59, 130, 246, 0.3)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: "1.25rem" }}>
          <div style={{ background: "var(--color-primary)", padding: "0.85rem", borderRadius: "12px", color: "white" }}>
            <ShieldCheck size={36} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <h1 style={{ fontSize: "1.6rem", fontWeight: 800, color: "#ffffff" }}>SKYGUARD AI</h1>
              <span className="brand-tag">Problem Statement: 26073</span>
            </div>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 600, color: "#93c5fd", marginTop: "0.2rem" }}>
              Intelligent Real-Time Anomaly Detection System for Temperature, Pressure, and Humidity Sensors in Automatic Weather Stations
            </h2>
            <p style={{ fontSize: "0.9rem", color: "var(--text-main)", marginTop: "0.75rem", lineHeight: 1.6 }}>
              "SkyGuard AI helps ensure that weather-station observations are trustworthy before they are used for forecasting, monitoring, agriculture, aviation, or disaster-management workflows."
            </p>
            <div style={{ marginTop: "0.6rem", fontSize: "0.85rem", fontWeight: 700, color: "#60a5fa" }}>
              Tagline: "Trust the data before you trust the forecast."
            </div>
          </div>
        </div>
      </div>

      {/* The Official Grand Challenge */}
      <div className="card" style={{ borderLeft: "4px solid #f59e0b" }}>
        <h3 className="card-title" style={{ color: "#fbbf24", marginBottom: "0.5rem" }}>
          <Award size={20} color="#f59e0b" /> Official Grand Challenge (Problem Statement 26073)
        </h3>
        <blockquote style={{ fontStyle: "italic", fontSize: "0.95rem", color: "var(--text-main)", background: "var(--bg-secondary)", padding: "1rem 1.25rem", borderRadius: "8px", borderLeft: "3px solid #f59e0b" }}>
          "Can AI build a self-aware and self-healing weather observation network capable of delivering trustworthy atmospheric data under all environmental conditions?"
        </blockquote>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.75rem", lineHeight: 1.5 }}>
          SkyGuard AI addresses this challenge through self-monitoring, real-time anomaly detection, evidence-backed explainable AI, sensor health degradation tracking, maintenance forecasting, and non-destructive AI-estimated expected value generation.
        </p>
      </div>

      {/* Technical Architecture & Input Restrictions */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem" }}>
        <div className="card">
          <h3 className="card-title">
            <Target size={18} color="#10b981" /> Meteorological Input Scope
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            The ML anomaly detection pipeline strictly adheres to the official problem scope using ONLY the three primary atmospheric parameters:
          </p>
          <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.5rem", fontSize: "0.85rem" }}>
            <li style={{ display: "flex", alignItems: "center", gap: "0.5rem", background: "var(--bg-secondary)", padding: "0.5rem 0.75rem", borderRadius: "6px" }}>
              <CheckCircle2 size={16} color="#10b981" /> <strong>Temperature (°C)</strong> — Ambient thermal readings
            </li>
            <li style={{ display: "flex", alignItems: "center", gap: "0.5rem", background: "var(--bg-secondary)", padding: "0.5rem 0.75rem", borderRadius: "6px" }}>
              <CheckCircle2 size={16} color="#10b981" /> <strong>Atmospheric Pressure (hPa)</strong> — Barometric pressure
            </li>
            <li style={{ display: "flex", alignItems: "center", gap: "0.5rem", background: "var(--bg-secondary)", padding: "0.5rem 0.75rem", borderRadius: "6px" }}>
              <CheckCircle2 size={16} color="#10b981" /> <strong>Relative Humidity (%)</strong> — Atmospheric moisture
            </li>
          </ul>
        </div>

        <div className="card">
          <h3 className="card-title">
            <Cpu size={18} color="#8b5cf6" /> Core Technology Stack
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", fontSize: "0.85rem" }}>
            <div style={{ background: "var(--bg-secondary)", padding: "0.6rem 0.75rem", borderRadius: "6px" }}>
              <div style={{ fontWeight: 700, color: "#8b5cf6" }}>Frontend</div>
              <div style={{ color: "var(--text-muted)", marginTop: "0.1rem" }}>React + Vite + Recharts</div>
            </div>
            <div style={{ background: "var(--bg-secondary)", padding: "0.6rem 0.75rem", borderRadius: "6px" }}>
              <div style={{ fontWeight: 700, color: "#8b5cf6" }}>Backend</div>
              <div style={{ color: "var(--text-muted)", marginTop: "0.1rem" }}>FastAPI + Async SQLAlchemy</div>
            </div>
            <div style={{ background: "var(--bg-secondary)", padding: "0.6rem 0.75rem", borderRadius: "6px" }}>
              <div style={{ fontWeight: 700, color: "#8b5cf6" }}>Machine Learning</div>
              <div style={{ color: "var(--text-muted)", marginTop: "0.1rem" }}>Isolation Forest + Model Feature Attribution</div>
            </div>
            <div style={{ background: "var(--bg-secondary)", padding: "0.6rem 0.75rem", borderRadius: "6px" }}>
              <div style={{ fontWeight: 700, color: "#8b5cf6" }}>Database</div>
              <div style={{ color: "var(--text-muted)", marginTop: "0.1rem" }}>Async SQLite / PostgreSQL</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
