"""
SkyGuard AI - Diagnostic Cause Classifier
Synthesizes ML Anomaly Score, Temporal Rule checks, Multivariate Coherence,
Spatial Consistency, and Seasonal/Diurnal Baseline Analysis into strict,
standardized meteorological diagnostics and multi-layer explainable evidence.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

NORMAL = "NORMAL"
PROBABLE_SENSOR_ANOMALY = "PROBABLE_SENSOR_ANOMALY"
POSSIBLE_GENUINE_WEATHER_EVENT = "POSSIBLE_GENUINE_WEATHER_EVENT"
POSSIBLE_COMMUNICATION_FAILURE = "POSSIBLE_COMMUNICATION_FAILURE"
POSSIBLE_DATA_QUALITY_ISSUE = "POSSIBLE_DATA_QUALITY_ISSUE"

@dataclass
class ClassificationResult:
    classification: str
    classification_label: str
    confidence: float
    anomaly_score: float
    affected_sensor: Optional[str]
    fault_type: Optional[str]
    reason: str
    evidence: Dict[str, Any]
    probable_cause: str
    recommended_action: str

class CauseClassifier:
    def classify(
        self,
        anomaly_score: float,
        temporal_findings: Dict,
        multivariate_result,
        spatial_result=None,
        seasonal_result=None,
        missing_data: bool = False,
        comm_failure: bool = False,
        anomaly_threshold: float = 0.35
    ) -> ClassificationResult:
        evidence = {}
        fault_types = []
        affected_sensors = []
        temporal_evidence_summary = []

        for sensor, findings in temporal_findings.items():
            for f in findings:
                fault_types.append(f.fault_type)
                affected_sensors.append(sensor)
                evidence[f"{sensor}_{f.fault_type}"] = {
                    "severity": round(f.severity, 2),
                    "description": f.description
                }
                if f.description:
                    temporal_evidence_summary.append(f.description)

        # 1. Temporal Evidence Breakdown
        evidence["temporal_evidence"] = {
            "flags_detected": len(fault_types),
            "fault_types": list(set(fault_types)),
            "summary": " ".join(temporal_evidence_summary) if temporal_evidence_summary else "No temporal rule violations detected."
        }

        # 2. Multivariate Evidence
        if multivariate_result:
            evidence["multivariate_consistency"] = {
                "coherent_change": multivariate_result.coherent_change,
                "isolated_sensor": multivariate_result.isolated_sensor,
                "weather_event_likelihood": round(multivariate_result.weather_event_likelihood, 2),
                "sensor_fault_likelihood": round(multivariate_result.sensor_fault_likelihood, 2),
                "description": multivariate_result.description
            }

        # 3. Spatial Evidence
        if spatial_result:
            evidence["spatial_consistency"] = {
                "spatial_anomaly": spatial_result.spatial_anomaly_detected,
                "regional_pattern": spatial_result.regional_pattern,
                "neighbor_count": spatial_result.neighbor_count,
                "temperature_delta": spatial_result.temperature_delta,
                "pressure_delta": spatial_result.pressure_delta,
                "humidity_delta": spatial_result.humidity_delta,
                "description": spatial_result.description
            }

        # 4. Seasonal / Diurnal Baseline Evidence
        if seasonal_result and seasonal_result.has_sufficient_history:
            evidence["seasonal_baseline"] = {
                "seasonal_anomaly_detected": seasonal_result.seasonal_anomaly_detected,
                "coherent_seasonal_shift": seasonal_result.coherent_seasonal_shift,
                "description": seasonal_result.description,
                "deviations": {
                    k: {
                        "observed": v.observed,
                        "expected_mean": v.expected_mean,
                        "z_score": v.z_score,
                        "is_outlier": v.is_seasonal_outlier,
                        "context": v.context,
                        "description": v.description
                    }
                    for k, v in seasonal_result.findings.items()
                }
            }

        is_ml_anomaly = anomaly_score >= anomaly_threshold

        if comm_failure:
            return ClassificationResult(
                classification=POSSIBLE_COMMUNICATION_FAILURE,
                classification_label="Possible Communication Failure",
                confidence=0.88,
                anomaly_score=max(anomaly_score, 0.85),
                affected_sensor=None,
                fault_type="communication_failure",
                reason="Extended telemetry packet drop detected across all AWS channels.",
                evidence=evidence,
                probable_cause="Data logger link failure or cellular/satellite modem disconnect.",
                recommended_action="Inspect station modem and power supply telemetry link."
            )

        if missing_data and not is_ml_anomaly and not fault_types:
            return ClassificationResult(
                classification=POSSIBLE_DATA_QUALITY_ISSUE,
                classification_label="Possible Data Quality Issue",
                confidence=0.72,
                anomaly_score=anomaly_score,
                affected_sensor=None,
                fault_type="missing_data",
                reason="Intermittent observation gaps recorded in data feed.",
                evidence=evidence,
                probable_cause="Packet loss or intermittent transducer power cycle.",
                recommended_action="Check station power voltage and buffer logs."
            )

        mv = multivariate_result
        coherent = mv.coherent_change if mv else False
        isolated = mv.isolated_sensor if mv else (affected_sensors[0] if affected_sensors else None)

        # Multi-parameter seasonal or temporal shift indicates synoptic weather passage
        coherent_seasonal = seasonal_result.coherent_seasonal_shift if (seasonal_result and seasonal_result.has_sufficient_history) else False

        # A real weather event exhibits either an ML anomaly, temporal rule flags, spatial anomaly,
        # seasonal deviation, or significant multi-sensor meteorological shift beyond quiet diurnal baseline
        has_significant_weather_shift = False
        if mv and mv.evidence and "normalized_changes" in mv.evidence:
            changes_dict = mv.evidence["normalized_changes"]
            if any(v >= 0.08 for v in changes_dict.values()) and sum(changes_dict.values()) >= 0.15:
                has_significant_weather_shift = True

        has_anomaly_trigger = (
            is_ml_anomaly or
            bool(fault_types) or
            (spatial_result and spatial_result.spatial_anomaly_detected) or
            (seasonal_result and seasonal_result.seasonal_anomaly_detected) or
            has_significant_weather_shift
        )

        # Spatial corroboration: peer AWS nodes verify whether anomaly is a regional weather phenomenon
        spatial_supported = (
            spatial_result is not None and
            spatial_result.regional_pattern == "SUPPORTED" and
            not spatial_result.spatial_anomaly_detected
        )

        # Distinguish genuine weather event vs sensor fault:
        # A legitimate meteorological event exhibits multi-sensor coherence, spatial peer agreement,
        # or coherent seasonal airmass transition, without isolated hardware failure signatures.
        is_weather_corroborated = (coherent or spatial_supported or coherent_seasonal)

        if is_weather_corroborated and has_anomaly_trigger and not (spatial_result and spatial_result.spatial_anomaly_detected):
            base_weather_likelihood = mv.weather_event_likelihood if mv else 0.2
            if coherent_seasonal:
                base_weather_likelihood = max(base_weather_likelihood, 0.75)
            conf = min(0.95, 0.65 + base_weather_likelihood)

            # Construct comprehensive meteorological reason
            reasons = []
            if spatial_supported and spatial_result:
                reasons.append(spatial_result.description)
            elif mv and mv.description:
                reasons.append(mv.description)
            if coherent_seasonal and seasonal_result:
                reasons.append(seasonal_result.description)

            reason = " ".join(reasons) if reasons else "Coordinated atmospheric variation matches a genuine meteorological event."

            return ClassificationResult(
                classification=POSSIBLE_GENUINE_WEATHER_EVENT,
                classification_label="Possible Genuine Meteorological Event",
                confidence=round(conf, 2),
                anomaly_score=anomaly_score,
                affected_sensor=None,
                fault_type="possible_genuine_weather_event",
                reason=reason,
                evidence=evidence,
                probable_cause="Possible Genuine Meteorological Event (corroborated by regional atmospheric observations / multi-sensor dynamics / seasonal airmass shift).",
                recommended_action="Cross-verify against adjacent AWS nodes and Doppler radar before dispatching field team."
            )

        if has_anomaly_trigger:
            primary_fault = fault_types[0] if fault_types else "multivariate_anomaly"
            if not fault_types and seasonal_result and seasonal_result.seasonal_anomaly_detected and not coherent_seasonal:
                primary_fault = "seasonal_baseline_outlier"
            
            # sensor_name must always be a string (isolated_sensor is a bool flag, not a name)
            sensor_name = (affected_sensors[0] if affected_sensors else (str(isolated) if isinstance(isolated, str) else "sensor"))
            
            # --- PHASE 5B: Multi-Evidence Derived Anomaly Confidence Calculation ---
            # Base confidence from statistical ML outlier score
            conf_components = []
            c_ml = min(0.35, anomaly_score * 0.40)
            conf_components.append(c_ml)

            # Temporal rule confidence contribution (spikes, flatlines, drift)
            c_temporal = 0.0
            if fault_types:
                # Up to 0.30 based on temporal severity
                max_sev = max([evidence[f"{s}_{f}"]["severity"] for s in temporal_findings for f in [item.fault_type for item in temporal_findings[s]]], default=0.5)
                c_temporal = min(0.30, 0.15 + max_sev * 0.15)
            conf_components.append(c_temporal)

            # Multivariate isolated sensor contribution
            c_mv = 0.15 if (mv and mv.isolated_sensor) else 0.05
            conf_components.append(c_mv)

            # Spatial contradiction contribution (peers remain normal while target deviates)
            c_spatial = 0.15 if (spatial_result and spatial_result.spatial_anomaly_detected) else 0.0
            conf_components.append(c_spatial)

            # Seasonal baseline deviation contribution
            c_seasonal = 0.10 if (seasonal_result and seasonal_result.seasonal_anomaly_detected and not coherent_seasonal) else 0.0
            conf_components.append(c_seasonal)

            raw_conf = 0.45 + sum(conf_components)
            conf = min(0.98, max(0.60, raw_conf))

            reason_parts = []
            if mv and mv.description:
                reason_parts.append(mv.description)
            for s, flist in temporal_findings.items():
                for item in flist:
                    if item.description:
                        reason_parts.append(item.description)
            if spatial_result and spatial_result.spatial_anomaly_detected:
                reason_parts.append(spatial_result.description)
            if seasonal_result and seasonal_result.seasonal_anomaly_detected and not coherent_seasonal:
                reason_parts.append(seasonal_result.description)
            
            reason = " ".join(reason_parts) if reason_parts else f"Unusual sensor pattern observed on {sensor_name}."
            
            action_map = {
                "spike": f"Inspect {sensor_name} transducer for electrical noise, grounding issues, or impulse damage.",
                "frozen_sensor": f"Examine {sensor_name} unit for physical blockage, icing, or frozen A/D converter.",
                "drift": f"Recalibrate {sensor_name} sensor; schedule drift offset correction.",
                "multivariate_anomaly": f"Verify calibration of {sensor_name} and check wiring integrity.",
                "seasonal_baseline_outlier": f"Check {sensor_name} calibration against local climatic normals."
            }

            return ClassificationResult(
                classification=PROBABLE_SENSOR_ANOMALY,
                classification_label="Probable Sensor Anomaly",
                confidence=round(conf, 2),
                anomaly_score=anomaly_score,
                affected_sensor=sensor_name,
                fault_type=primary_fault,
                reason=reason,
                evidence=evidence,
                probable_cause=f"Probable {sensor_name.title()} Sensor Anomaly ({primary_fault.replace('_', ' ')})",
                recommended_action=action_map.get(primary_fault, f"Inspect and recalibrate {sensor_name} sensor.")
            )

        return ClassificationResult(
            classification=NORMAL,
            classification_label="Normal Operations",
            confidence=0.95,
            anomaly_score=anomaly_score,
            affected_sensor=None,
            fault_type=None,
            reason="All sensor readings track historical distribution and cross-validation bounds.",
            evidence=evidence,
            probable_cause="",
            recommended_action="Normal operations. No intervention required."
        )
