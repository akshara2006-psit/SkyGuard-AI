"""
SkyGuard AI - Sensor Health & Maintenance Intelligence Engine
Computes transparent, deterministic degradation scores, tracks health trends (Stable vs Declining),
and generates evidence-backed maintenance recommendations.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class HealthState:
    sensor: str
    health_score: float
    status: str
    degradation_trend: str
    maintenance_status: str
    maintenance_recommendation: str
    maintenance_reasons: List[str]
    recent_anomaly_count: int
    missing_data_rate: float
    consistency_score: float
    fault_history_count: int
    explanation: str

def compute_health_score(
    recent_count: int,
    total_readings: int,
    missing_readings: int,
    fault_history_count: int
) -> float:
    """
    Deterministic health score formula [5.0, 100.0].
    Applies empirical penalties for recent anomaly frequency, missing data, and historical faults.
    """
    total = max(total_readings, 1)
    missing_rate = missing_readings / total
    score = 100.0
    
    # Anomaly frequency penalty (max 35 pts)
    anomaly_ratio = recent_count / max(total, 10)
    score -= min(35.0, anomaly_ratio * 60.0)
    
    # Missing telemetry penalty (max 25 pts)
    score -= min(25.0, missing_rate * 40.0)
    
    # Historical fault count penalty (max 20 pts)
    score -= min(20.0, fault_history_count * 1.2)
    
    return round(max(5.0, min(100.0, score)), 1)

class SensorHealthEngine:
    """
    Engine calculating sensor-specific and station-level health states,
    degradation trends, and maintenance recommendations.
    """
    def update_health(
        self,
        sensor: str,
        recent_anomalies: List[Dict[str, Any]],
        total_readings: int,
        missing_readings: int,
        fault_history_count: int,
        previous_health_score: Optional[float] = None
    ) -> HealthState:
        total = max(total_readings, 1)
        recent_count = len(recent_anomalies)
        missing_rate = missing_readings / total
        consistency = max(0.0, 1.0 - (recent_count / total))

        score = compute_health_score(recent_count, total_readings, missing_readings, fault_history_count)

        # 1. Determine Degradation Trend (STABLE, DECLINING, IMPROVING)
        if previous_health_score is not None:
            delta = score - previous_health_score
            if delta < -4.0:
                degradation_trend = "DECLINING"
            elif delta > +4.0:
                degradation_trend = "IMPROVING"
            else:
                degradation_trend = "STABLE"
        else:
            degradation_trend = "DECLINING" if score < 85.0 else "STABLE"

        # 2. Determine Health Status
        if score >= 85.0:
            status = "HEALTHY"
        elif score >= 65.0:
            status = "WARNING"
        elif score >= 40.0:
            status = "DEGRADED"
        else:
            status = "CRITICAL"

        # 3. Determine Maintenance Recommendation & Evidence Reasons
        maintenance_reasons = []
        if recent_count > 0:
            maintenance_reasons.append(f"{recent_count} anomaly event(s) recorded in recent observation window")
        if missing_rate > 0.05:
            maintenance_reasons.append(f"Telemetry missing data rate at {round(missing_rate * 100, 1)}%")
        if fault_history_count > 2:
            maintenance_reasons.append(f"Cumulative fault history count: {fault_history_count} events")
        if degradation_trend == "DECLINING":
            maintenance_reasons.append("Sensor health score exhibiting a declining trend over recent window")

        if score < 35.0 or missing_rate > 0.40:
            maint_status = "URGENT_REPLACEMENT"
            maint_rec = f"Immediate hardware inspection or replacement required for {sensor} transducer."
        elif score < 50.0 or (degradation_trend == "DECLINING" and score < 65.0):
            maint_status = "MAINTENANCE_REQUIRED"
            maint_rec = f"Schedule technician maintenance and recalibration for {sensor} sensor."
        elif score < 75.0 or degradation_trend == "DECLINING":
            maint_status = "INSPECTION_RECOMMENDED"
            maint_rec = f"Preventative technician inspection recommended for {sensor} unit."
        else:
            maint_status = "NOMINAL_MONITORING"
            maint_rec = f"Nominal operations for {sensor} sensor. Routine monitoring."

        if not maintenance_reasons:
            maintenance_reasons.append("Telemetry operates strictly within learned baseline parameters")

        # 4. Generate Narrative Explanation
        explanation = f"{sensor.capitalize()} sensor health is {score}% ({status}, {degradation_trend} trend). {maint_rec}"

        return HealthState(
            sensor=sensor,
            health_score=score,
            status=status,
            degradation_trend=degradation_trend,
            maintenance_status=maint_status,
            maintenance_recommendation=maint_rec,
            maintenance_reasons=maintenance_reasons,
            recent_anomaly_count=recent_count,
            missing_data_rate=round(missing_rate, 3),
            consistency_score=round(consistency, 3),
            fault_history_count=fault_history_count,
            explanation=explanation
        )
