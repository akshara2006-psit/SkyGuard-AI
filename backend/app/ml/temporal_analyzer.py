"""
SkyGuard AI - Temporal Analyzer
Performs rule-based checks: Spikes, Frozen sensors, Drift, Missing data, Telemetry loss.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class TemporalFinding:
    detected: bool
    fault_type: str
    sensor: Optional[str]
    severity: float  # 0.0 - 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

class TemporalAnalyzer:
    def __init__(
        self,
        spike_std_threshold: float = 3.5,
        frozen_tolerance: float = 0.05,
        frozen_window: int = 12,
        drift_window: int = 15,
        drift_slope_threshold: float = 0.25,
        pressure_frozen_window: int = 24
    ):
        self.spike_std_threshold = spike_std_threshold
        self.frozen_tolerance = frozen_tolerance
        self.frozen_window = frozen_window
        self.drift_window = drift_window
        self.drift_slope_threshold = drift_slope_threshold
        self.pressure_frozen_window = pressure_frozen_window

    def check_spike(self, values: pd.Series, sensor: str) -> TemporalFinding:
        clean = values.dropna()
        if len(clean) < 4:
            return TemporalFinding(False, "spike", sensor, 0.0)

        current = float(clean.iloc[-1])
        baseline = clean.iloc[-min(12, len(clean)):-1]
        if len(baseline) < 2:
            return TemporalFinding(False, "spike", sensor, 0.0)

        mean = float(baseline.mean())
        std = max(float(baseline.std()), 0.05)
        z_score = abs(current - mean) / std

        detected = bool(z_score >= self.spike_std_threshold)
        severity = float(min(1.0, (z_score - self.spike_std_threshold + 1) / 5.0)) if detected else 0.0

        desc = (
            f"{sensor.capitalize()} value of {current:.2f} abruptly deviates by {z_score:.1f} sigma "
            f"from recent baseline of {mean:.2f}."
        ) if detected else ""

        return TemporalFinding(
            detected=detected,
            fault_type="spike",
            sensor=sensor,
            severity=round(severity, 3),
            evidence={"current": current, "baseline_mean": round(mean, 2), "z_score": round(z_score, 2)},
            description=desc
        )

    def check_frozen(self, values: pd.Series, sensor: str) -> TemporalFinding:
        eff_window = self.pressure_frozen_window if sensor == "pressure" else self.frozen_window
        clean = values.dropna().tail(eff_window)
        if len(clean) < eff_window:
            return TemporalFinding(False, "frozen_sensor", sensor, 0.0)

        std = float(clean.std())
        detected = bool(std < self.frozen_tolerance)
        severity = float(max(0.0, 1.0 - (std / self.frozen_tolerance))) if detected else 0.0

        desc = (
            f"{sensor.capitalize()} sensor shows near-zero variability (std={std:.4f}) "
            f"over the past {eff_window} readings, indicating a frozen/stuck state."
        ) if detected else ""

        return TemporalFinding(
            detected=detected,
            fault_type="frozen_sensor",
            sensor=sensor,
            severity=round(severity, 3),
            evidence={"std": round(std, 5), "window": eff_window},
            description=desc
        )

    def check_drift(self, values: pd.Series, sensor: str) -> TemporalFinding:
        clean = values.dropna().tail(self.drift_window)
        if len(clean) < max(8, self.drift_window // 2):
            return TemporalFinding(False, "drift", sensor, 0.0)

        x = np.arange(len(clean))
        slope, _ = np.polyfit(x, clean.values, 1)
        detected = bool(abs(slope) > self.drift_slope_threshold)
        severity = float(min(1.0, abs(slope) / (self.drift_slope_threshold * 2.5))) if detected else 0.0

        desc = (
            f"{sensor.capitalize()} exhibits consistent linear drift at {slope:+.3f} units/sample."
        ) if detected else ""

        return TemporalFinding(
            detected=detected,
            fault_type="drift",
            sensor=sensor,
            severity=round(severity, 3),
            evidence={"slope": round(float(slope), 4)},
            description=desc
        )

    def analyze(self, df: pd.DataFrame) -> Dict[str, List[TemporalFinding]]:
        results = {}
        for sensor in ['temperature', 'pressure', 'humidity']:
            if sensor not in df.columns:
                continue
            findings = []
            values = df[sensor]
            
            spike = self.check_spike(values, sensor)
            if spike.detected:
                findings.append(spike)
            frozen = self.check_frozen(values, sensor)
            if frozen.detected:
                findings.append(frozen)
            drift = self.check_drift(values, sensor)
            if drift.detected:
                findings.append(drift)

            results[sensor] = findings
        return results
