"""
SkyGuard AI - Multivariate Cross-Sensor Consistency Analyzer
Distinguishes single sensor faults from coordinated meteorological events.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class MultivariateResult:
    coherent_change: bool
    isolated_sensor: Optional[str]
    weather_event_likelihood: float
    sensor_fault_likelihood: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

class MultivariateAnalyzer:
    def analyze(self, df: pd.DataFrame, window: int = 6) -> MultivariateResult:
        sensors = ['temperature', 'pressure', 'humidity']
        available = [s for s in sensors if s in df.columns and df[s].notna().sum() >= 3]

        if len(available) < 2:
            return MultivariateResult(
                coherent_change=False,
                isolated_sensor=None,
                weather_event_likelihood=0.3,
                sensor_fault_likelihood=0.5,
                description="Insufficient multi-sensor history for cross-validation."
            )

        recent = df[available].tail(window)
        typical_ranges = {'temperature': 20.0, 'pressure': 15.0, 'humidity': 35.0}

        changes = {}
        for s in available:
            delta = float(recent[s].diff().abs().mean())
            changes[s] = float(delta / typical_ranges.get(s, 20.0))

        active = [s for s in available if changes[s] > 0.02]
        max_s = max(changes, key=changes.get) if changes else None
        max_val = changes.get(max_s, 0.0) if max_s else 0.0
        
        other_vals = [changes[s] for s in available if s != max_s]
        avg_others = float(np.mean(other_vals)) if other_vals else 0.0

        coherent = bool(len(active) >= 2 and (avg_others > 0.015 and max_val < avg_others * 3.5))
        isolated = str(max_s) if (max_val > 0.04 and max_val >= avg_others * 3.0) else None

        if coherent:
            weather_likelihood = 0.70
            fault_likelihood = 0.20
            desc = (
                f"Multi-sensor coherence detected: Simultaneous shifts across {', '.join(active)} "
                "align with a genuine meteorological event (e.g. front or storm)."
            )
        elif isolated:
            weather_likelihood = 0.15
            fault_likelihood = 0.85
            desc = (
                f"Disproportionate anomaly in {isolated} while companion sensors remain baseline-stable, "
                f"strongly indicating a localized sensor malfunction."
            )
        else:
            weather_likelihood = 0.35
            fault_likelihood = 0.45
            desc = "Mixed sensor dynamics; indeterminate cross-correlation."

        return MultivariateResult(
            coherent_change=coherent,
            isolated_sensor=isolated,
            weather_event_likelihood=weather_likelihood,
            sensor_fault_likelihood=fault_likelihood,
            evidence={"normalized_changes": {k: round(v, 4) for k, v in changes.items()}, "active_count": len(active)},
            description=desc
        )
