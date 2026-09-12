"""
SkyGuard AI - Core API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import json
import logging

from ..database.connection import get_db
from ..models.db_models import Station, SensorReading, Anomaly, SensorHealth, Alert
from ..services import station_service
from ..ml.analyzer import SkyGuardAnalyzer
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

_analyzer: Optional[SkyGuardAnalyzer] = None

def get_analyzer() -> SkyGuardAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SkyGuardAnalyzer(settings.MODEL_PATH)
    return _analyzer

def station_to_dict(s: Station) -> Dict[str, Any]:
    source = "NOAA_ASOS" if (s.location_desc and "NOAA_ASOS" in s.location_desc) else "DEMO_SIMULATION"
    return {
        "id": s.id,
        "name": s.name,
        "latitude": s.latitude,
        "longitude": s.longitude,
        "elevation": s.elevation,
        "location_desc": s.location_desc,
        "source": source,
        "is_active": s.is_active,
    }

def reading_to_dict(r: SensorReading) -> Dict[str, Any]:
    return {
        "id": r.id,
        "station_id": r.station_id,
        "timestamp": r.timestamp.isoformat(),
        "temperature": r.temperature,
        "pressure": r.pressure,
        "humidity": r.humidity,
        "is_missing": r.is_missing,
        "data_quality": r.data_quality,
    }

def anomaly_to_dict(a: Anomaly) -> Dict[str, Any]:
    ev = {}
    if a.evidence:
        try:
            ev = json.loads(a.evidence)
        except Exception:
            ev = {}

    # Phase 5B: extract corrected value suggestions from stored evidence (ESTIMATED/OPTIONAL)
    corrected_values: Dict[str, Any] = {}
    corrected_temperature = None
    corrected_pressure = None
    corrected_humidity = None
    explainable_evidence: Dict[str, Any] = {}

    if ev:
        # corrected_values may be stored inside evidence dict by the pipeline
        corrected_values = ev.get("corrected_values", {})
        explainable_evidence = ev.get("explainable_evidence", {})
        if corrected_values:
            t_corr = corrected_values.get("temperature", {})
            corrected_temperature = t_corr.get("corrected_value") if isinstance(t_corr, dict) else None
            p_corr = corrected_values.get("pressure", {})
            corrected_pressure = p_corr.get("corrected_value") if isinstance(p_corr, dict) else None
            h_corr = corrected_values.get("humidity", {})
            corrected_humidity = h_corr.get("corrected_value") if isinstance(h_corr, dict) else None

    return {
        "id": a.id,
        "station_id": a.station_id,
        "timestamp": a.timestamp.isoformat(),
        "anomaly_score": a.anomaly_score,
        "anomaly_score_pct": round(a.anomaly_score * 100, 1),
        "is_anomaly": a.is_anomaly,
        "classification": a.classification,
        "confidence": a.confidence,
        "confidence_pct": round((a.confidence or 0) * 100, 1),
        "affected_sensor": a.affected_sensor,
        "fault_type": a.fault_type,
        "observed_temperature": a.observed_temperature,
        "expected_temperature": a.expected_temperature,
        "observed_pressure": a.observed_pressure,
        "expected_pressure": a.expected_pressure,
        "observed_humidity": a.observed_humidity,
        "expected_humidity": a.expected_humidity,
        "reason": a.reason,
        "evidence": ev,
        "probable_cause": a.probable_cause,
        "recommended_action": a.recommended_action,
        # Phase 5B — corrected values (ESTIMATED/OPTIONAL, never overwrites raw observation)
        "corrected_values": corrected_values,
        "corrected_temperature": corrected_temperature,
        "corrected_pressure": corrected_pressure,
        "corrected_humidity": corrected_humidity,
        "explainable_evidence": explainable_evidence,
    }

def health_to_dict(h: SensorHealth) -> Dict[str, Any]:
    reasons = []
    if getattr(h, 'maintenance_reasons', None):
        try:
            reasons = json.loads(h.maintenance_reasons)
        except Exception:
            reasons = [h.maintenance_reasons]
    return {
        "station_id": h.station_id,
        "sensor_type": h.sensor_type,
        "health_score": h.health_score,
        "status": h.status,
        "degradation_trend": getattr(h, 'degradation_trend', 'STABLE') or 'STABLE',
        "maintenance_status": getattr(h, 'maintenance_status', 'NOMINAL_MONITORING') or 'NOMINAL_MONITORING',
        "maintenance_recommendation": getattr(h, 'maintenance_recommendation', None) or f"Nominal operations for {h.sensor_type} sensor.",
        "maintenance_reasons": reasons,
        "recent_anomaly_count": h.recent_anomaly_count,
        "missing_data_rate": h.missing_data_rate,
        "consistency_score": h.consistency_score,
        "fault_history_count": h.fault_history_count,
        "timestamp": h.timestamp.isoformat() if h.timestamp else None,
    }

def alert_to_dict(a: Alert) -> Dict[str, Any]:
    return {
        "id": a.id,
        "station_id": a.station_id,
        "anomaly_id": a.anomaly_id,
        "timestamp": a.timestamp.isoformat(),
        "severity": a.severity,
        "sensor": a.sensor,
        "title": a.title,
        "message": a.message,
        "probable_cause": a.probable_cause,
        "confidence": a.confidence,
        "recommended_action": a.recommended_action,
        "status": a.status,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
    }

# ---- ENDPOINTS ----

@router.get("/stations")
async def get_stations(db: AsyncSession = Depends(get_db)):
    stations = await station_service.get_all_stations(db)
    result = []
    for s in stations:
        d = station_to_dict(s)
        readings = await station_service.get_recent_readings(db, s.id, limit=1)
        if readings:
            r = readings[0]
            d["last_temperature"] = r.temperature
            d["last_pressure"] = r.pressure
            d["last_humidity"] = r.humidity
            d["last_reading_time"] = r.timestamp.isoformat()
        health = await station_service.get_station_health(db, s.id)
        overall = next((h for h in health if h.sensor_type == 'overall'), None)
        d["health_score"] = overall.health_score if overall else 100.0
        d["health_status"] = overall.status if overall else "HEALTHY"
        result.append(d)
    return result

@router.get("/stations/{station_id}")
async def get_station(station_id: str, db: AsyncSession = Depends(get_db)):
    station = await station_service.get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Station {station_id} not found")
    d = station_to_dict(station)
    readings = await station_service.get_recent_readings(db, station_id, limit=1)
    if readings:
        r = readings[0]
        d["last_temperature"] = r.temperature
        d["last_pressure"] = r.pressure
        d["last_humidity"] = r.humidity
        d["last_reading_time"] = r.timestamp.isoformat()
    health = await station_service.get_station_health(db, station_id)
    overall = next((h for h in health if h.sensor_type == 'overall'), None)
    d["health_score"] = overall.health_score if overall else 100.0
    d["health_status"] = overall.status if overall else "HEALTHY"
    d["health"] = [health_to_dict(h) for h in health]
    return d

@router.get("/stations/{station_id}/readings")
async def get_readings(
    station_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    readings = await station_service.get_recent_readings(db, station_id, limit=limit)
    return [reading_to_dict(r) for r in readings]

@router.get("/stations/{station_id}/anomalies")
async def get_station_anomalies(
    station_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    anomalies = await station_service.get_station_anomalies(db, station_id, limit=limit)
    return [anomaly_to_dict(a) for a in anomalies]

@router.get("/stations/{station_id}/health")
async def get_health(
    station_id: str,
    db: AsyncSession = Depends(get_db)
):
    health = await station_service.get_station_health(db, station_id)
    return [health_to_dict(h) for h in health]

@router.get("/anomalies")
async def get_anomalies(limit: int = 100, db: AsyncSession = Depends(get_db)):
    anomalies = await station_service.get_all_anomalies(db, limit=limit)
    return [anomaly_to_dict(a) for a in anomalies]

@router.get("/alerts")
async def get_alerts(
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    alerts = await station_service.get_all_alerts(db, limit=limit, status=status)
    return [alert_to_dict(a) for a in alerts]

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    alert = await station_service.acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": alert_id}

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    return await station_service.get_summary(db)

@router.post("/analyze")
async def analyze_reading(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    station_id = payload.get("station_id")
    if not station_id:
        raise HTTPException(status_code=400, detail="station_id required")

    recent = await station_service.get_recent_readings(db, station_id, limit=50)
    recent_records = [reading_to_dict(r) for r in recent]

    analyzer = get_analyzer()
    result = analyzer.analyze_reading(recent_records, station_id, payload)
    return result

@router.get("/evaluation")
async def get_evaluation():
    """Returns cached or freshly computed model evaluation metrics."""
    from ..ml.evaluator import get_latest_evaluation
    return get_latest_evaluation()

@router.post("/evaluation/run")
async def trigger_evaluation():
    """Triggers a live evaluation run across the ground-truth benchmark dataset."""
    from ..ml.evaluator import run_evaluation
    result = run_evaluation()
    return result

