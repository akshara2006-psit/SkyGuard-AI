"""
SkyGuard AI - Optional Corrected / Imputed Value Engine
Suggests physically plausible and explainable corrected values for anomalous observations.

Strict Safety Rules:
1. Never overwrites raw observation data.
2. Returns null / None if evidence is insufficient rather than inventing values.
3. Clearly marks all suggested values as OPTIONAL / ESTIMATED.
4. Uses multi-tier evidence synthesis:
   - Tier 1: Peer AWS spatial corroboration mean (local atmospheric state)
   - Tier 2: Learned diurnal / seasonal baseline envelope
   - Tier 3: Pre-anomaly autoregressive rolling short-term persistence
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CorrectedValueSuggestion:
    is_corrected: bool
    status: str # "ESTIMATED_OPTIONAL" | "NO_CORRECTION_NEEDED" | "INSUFFICIENT_EVIDENCE"
    method: str
    confidence: float
    raw_value: Optional[float]
    corrected_value: Optional[float]
    expected_range: Optional[tuple]
    explanation: str

class ValueCorrector:
    """
    Computes optional corrected/imputed values for temperature, pressure, and humidity
    when an observation is classified as a sensor anomaly.
    """

    def suggest_corrections(
        self,
        classification: str,
        affected_sensor: Optional[str],
        latest_record: Dict[str, Any],
        recent_df,
        seasonal_result=None,
        spatial_result=None
    ) -> Dict[str, Any]:
        """
        Evaluates whether a sensor anomaly warrants a suggested corrected value.
        For normal observations or legitimate weather events, no correction is applied.
        """
        sensors = ["temperature", "pressure", "humidity"]
        suggestions = {}

        is_sensor_fault = classification in [
            "PROBABLE_SENSOR_ANOMALY",
            "PROBABLE_SENSOR_FAULT"
        ]

        for s in sensors:
            raw_val = latest_record.get(s)
            
            # If observation is normal or this sensor is not anomalous, no correction is needed
            if not is_sensor_fault or (affected_sensor and affected_sensor != s):
                suggestions[s] = {
                    "is_corrected": False,
                    "status": "NO_CORRECTION_NEEDED",
                    "method": "RAW_OBSERVATION_PRESERVED",
                    "confidence": 1.0,
                    "raw_value": raw_val,
                    "corrected_value": None,
                    "is_estimated_optional": False,
                    "explanation": f"Raw {s} observation is nominal or part of a legitimate meteorological pattern."
                }
                continue

            # If this is an anomalous sensor reading, attempt evidence-based imputation
            corrected_val = None
            method = "INSUFFICIENT_EVIDENCE"
            method_conf = 0.0
            explanation = f"Insufficient evidence to safely suggest an estimated {s} value."

            # Strategy 1: Peer Spatial Consensus (strongest evidence)
            if spatial_result and spatial_result.neighbor_count > 0:
                # If peer stations exist and delta is known
                delta_map = {
                    "temperature": spatial_result.temperature_delta,
                    "pressure": spatial_result.pressure_delta,
                    "humidity": spatial_result.humidity_delta
                }
                delta = delta_map.get(s, 0.0)
                if delta > 0.0 and raw_val is not None:
                    # Impute using the average of peer stations: target - signed delta
                    # Determine direction from raw vs delta
                    # If target is above peer average, peer_avg = raw - delta
                    peer_avg = raw_val - delta if raw_val > delta else raw_val + delta
                    corrected_val = round(peer_avg, 2)
                    method = "SPATIAL_PEER_CONSENSUS"
                    method_conf = 0.90
                    explanation = (
                        f"Suggested correction based on average of {spatial_result.neighbor_count} "
                        f"geographically proximate AWS peer stations (baseline ~{corrected_val})."
                    )

            # Strategy 2: Seasonal / Diurnal Baseline Expected Mean
            if corrected_val is None and seasonal_result and seasonal_result.has_sufficient_history:
                finding = seasonal_result.findings.get(s)
                if finding and finding.expected_mean is not None:
                    corrected_val = round(finding.expected_mean, 2)
                    method = "SEASONAL_DIURNAL_BASELINE"
                    method_conf = 0.82
                    explanation = (
                        f"Suggested correction derived from learned diurnal profile for {finding.context} "
                        f"(expected {finding.expected_mean} +/- {finding.expected_std*2:.1f})."
                    )

            # Strategy 3: Pre-anomaly short-term persistence (rolling baseline prior to spike/step)
            if corrected_val is None and recent_df is not None and not recent_df.empty and s in recent_df.columns:
                series = recent_df[s].dropna()
                if len(series) >= 4:
                    # Take median of the 3-6 readings preceding latest sample
                    pre_anomaly_baseline = float(series.iloc[-min(7, len(series)):-1].median())
                    corrected_val = round(pre_anomaly_baseline, 2)
                    method = "TEMPORAL_PERSISTENCE_INTERPOLATION"
                    method_conf = 0.75
                    explanation = (
                        f"Suggested correction estimated from rolling pre-anomaly baseline "
                        f"prior to the sudden deviation (median ~{corrected_val})."
                    )

            if corrected_val is not None:
                suggestions[s] = {
                    "is_corrected": True,
                    "status": "ESTIMATED_OPTIONAL",
                    "method": method,
                    "confidence": method_conf,
                    "raw_value": raw_val,
                    "corrected_value": corrected_val,
                    "is_estimated_optional": True,
                    "explanation": f"[ESTIMATED/OPTIONAL] {explanation}"
                }
            else:
                suggestions[s] = {
                    "is_corrected": False,
                    "status": "INSUFFICIENT_EVIDENCE",
                    "method": "NO_IMPUTATION",
                    "confidence": 0.0,
                    "raw_value": raw_val,
                    "corrected_value": None,
                    "is_estimated_optional": False,
                    "explanation": explanation
                }

        return suggestions
