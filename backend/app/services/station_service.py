from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models.db_models import Station, SensorReading, Anomaly, SensorHealth, Alert
import logging
logger = logging.getLogger(__name__)

async def get_all_stations(db):
    result = await db.execute(select(Station).where(Station.is_active == True))
    return result.scalars().all()

async def get_station(db, station_id):
    result = await db.execute(select(Station).where(Station.id == station_id))
    return result.scalar_one_or_none()

async def upsert_station(db, station_data):
    existing = await get_station(db, station_data["id"])
    if existing:
        for k, v in station_data.items(): setattr(existing, k, v)
        station = existing
    else:
        station = Station(**station_data); db.add(station)
    await db.commit(); await db.refresh(station); return station

async def add_reading(db, reading_data):
    reading = SensorReading(**reading_data); db.add(reading)
    await db.commit(); await db.refresh(reading); return reading

async def get_recent_readings(db, station_id, limit=100):
    result = await db.execute(
        select(SensorReading).where(SensorReading.station_id == station_id)
        .order_by(SensorReading.timestamp.desc()).limit(limit))
    return list(reversed(result.scalars().all()))

async def get_station_anomalies(db, station_id, limit=50):
    result = await db.execute(
        select(Anomaly).where(Anomaly.station_id == station_id)
        .order_by(Anomaly.timestamp.desc()).limit(limit))
    return result.scalars().all()

async def get_all_anomalies(db, limit=100):
    result = await db.execute(
        select(Anomaly).where(Anomaly.is_anomaly == True)
        .order_by(Anomaly.timestamp.desc()).limit(limit))
    return result.scalars().all()

async def save_anomaly(db, anomaly_data):
    a = Anomaly(**anomaly_data); db.add(a)
    await db.commit(); await db.refresh(a); return a

async def get_station_health(db, station_id):
    result = await db.execute(
        select(SensorHealth).where(SensorHealth.station_id == station_id)
        .order_by(SensorHealth.timestamp.desc()))
    seen = set(); records = []
    for h in result.scalars().all():
        if h.sensor_type not in seen: records.append(h); seen.add(h.sensor_type)
    return records

async def upsert_health(db, station_id, sensor_type, health_data):
    result = await db.execute(
        select(SensorHealth).where(SensorHealth.station_id == station_id,
        SensorHealth.sensor_type == sensor_type)
        .order_by(SensorHealth.timestamp.desc()).limit(1))
    existing = result.scalar_one_or_none()
    if existing:
        for k, v in health_data.items(): setattr(existing, k, v)
        existing.timestamp = datetime.utcnow()
    else:
        obj = SensorHealth(station_id=station_id, sensor_type=sensor_type,
                           timestamp=datetime.utcnow(), **health_data)
        db.add(obj)
    await db.commit()

async def get_all_alerts(db, limit=100, status=None):
    q = select(Alert).order_by(Alert.timestamp.desc())
    if status: q = q.where(Alert.status == status)
    result = await db.execute(q.limit(limit)); return result.scalars().all()

async def save_alert(db, alert_data):
    a = Alert(**alert_data)
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a

async def acknowledge_alert(db, alert_id):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert:
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.utcnow()
        await db.commit()
    return alert

async def get_open_alert(db, station_id: str, sensor: Optional[str] = None):
    q = select(Alert).where(Alert.station_id == station_id, Alert.status == "OPEN")
    if sensor:
        q = q.where(Alert.sensor == sensor)
    else:
        q = q.where(Alert.sensor.is_(None))
    result = await db.execute(q.order_by(Alert.timestamp.desc()).limit(1))
    return result.scalar_one_or_none()

async def resolve_alerts_for_sensor(db, station_id: str, sensor: Optional[str] = None):
    q = select(Alert).where(Alert.station_id == station_id, Alert.status == "OPEN")
    if sensor:
        q = q.where(Alert.sensor == sensor)
    result = await db.execute(q)
    alerts = result.scalars().all()
    now = datetime.utcnow()
    for a in alerts:
        a.status = "RESOLVED"
        a.resolved_at = now
    if alerts:
        await db.commit()
    return alerts

async def get_summary(db):
    stations_result = await db.execute(select(Station).where(Station.is_active == True))
    stations = stations_result.scalars().all()
    total = len(stations)
    healthy = warning = degraded = critical = 0
    for station in stations:
        health = await get_station_health(db, station.id)
        overall = next((h for h in health if h.sensor_type == "overall"), None)
        if overall:
            if overall.status == "HEALTHY":
                healthy += 1
            elif overall.status == "WARNING":
                warning += 1
            elif overall.status == "DEGRADED":
                degraded += 1
            elif overall.status == "CRITICAL":
                critical += 1
            else:
                healthy += 1
        else:
            healthy += 1

    since = datetime.utcnow() - timedelta(hours=24)
    # Hardware/operational anomaly count in last 24h
    ra = await db.execute(select(func.count(Anomaly.id)).where(
        Anomaly.is_anomaly == True,
        Anomaly.timestamp >= since,
        Anomaly.classification.in_([
            "PROBABLE_SENSOR_ANOMALY",
            "PROBABLE_SENSOR_FAULT",
            "POSSIBLE_COMMUNICATION_FAILURE",
            "POSSIBLE_DATA_QUALITY_ISSUE"
        ])
    ))
    oa = await db.execute(select(func.count(Alert.id)).where(Alert.status == "OPEN"))
    anom_count = ra.scalar() or 0
    open_alerts_count = oa.scalar() or 0

    return {
        "total_stations": total,
        "healthy": healthy,
        "warning": warning,
        "degraded": degraded,
        "critical": critical,
        "anomaly": degraded + critical,
        "active_anomalies": anom_count,
        "recent_anomalies_24h": anom_count,
        "open_alerts": open_alerts_count,
        "offline": 0
    }
