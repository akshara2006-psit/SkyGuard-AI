"""
SkyGuard AI - Simulation Service
Simulates AWS observations arriving over time with realistic patterns and fault injection.
"""
import asyncio
import random
import math
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import AsyncSessionLocal
from ..models.db_models import Station, SensorReading, Anomaly, Alert
from ..services import station_service
from ..ml.analyzer import SkyGuardAnalyzer
from ..ml.health_engine import SensorHealthEngine
from ..config import settings

logger = logging.getLogger(__name__)

# Realistic AWS station definitions
STATIONS = [
    {"id": "AWS-001", "name": "Delhi Safdarjung", "latitude": 28.5665, "longitude": 77.2000, "elevation": 216.0, "location_desc": "Central Delhi"},
    {"id": "AWS-002", "name": "Mumbai Colaba", "latitude": 18.9067, "longitude": 72.8147, "elevation": 11.0, "location_desc": "Western Coast"},
    {"id": "AWS-003", "name": "Chennai Nungambakkam", "latitude": 13.0827, "longitude": 80.2707, "elevation": 16.0, "location_desc": "South India Coast"},
    {"id": "AWS-004", "name": "Kolkata Alipore", "latitude": 22.5354, "longitude": 88.3372, "elevation": 6.0, "location_desc": "East India Delta"},
    {"id": "AWS-005", "name": "Bengaluru HAL", "latitude": 12.9716, "longitude": 77.5946, "elevation": 921.0, "location_desc": "Deccan Plateau"},
    {"id": "AWS-006", "name": "Hyderabad Begumpet", "latitude": 17.4400, "longitude": 78.4700, "elevation": 545.0, "location_desc": "Central Plateau"},
]

# Seasonal baseline: temperature for each station (rough monsoon-summer averages)
STATION_BASELINES = {
    "AWS-001": {"temp": 30.0, "pressure": 1005.0, "humidity": 65.0, "temp_diurnal": 8.0},
    "AWS-002": {"temp": 30.0, "pressure": 1008.0, "humidity": 80.0, "temp_diurnal": 4.0},
    "AWS-003": {"temp": 29.0, "pressure": 1007.0, "humidity": 75.0, "temp_diurnal": 5.0},
    "AWS-004": {"temp": 30.0, "pressure": 1007.0, "humidity": 78.0, "temp_diurnal": 6.0},
    "AWS-005": {"temp": 24.0, "pressure": 912.0, "humidity": 60.0, "temp_diurnal": 9.0},
    "AWS-006": {"temp": 27.0, "pressure": 950.0, "humidity": 55.0, "temp_diurnal": 8.0},
}


class StationSimulator:
    """Simulates a single AWS station's sensor behaviour."""

    def __init__(self, station_id: str):
        self.station_id = station_id
        self.baseline = STATION_BASELINES.get(station_id, {"temp": 28.0, "pressure": 1005.0, "humidity": 65.0, "temp_diurnal": 6.0})
        self.step = 0
        self.fault_mode: Optional[str] = None
        self.fault_steps_remaining = 0
        self.drift_offset = 0.0
        self._frozen_values: Optional[Dict] = None

    def set_fault(self, fault_type: str, duration_steps: int = 10):
        self.fault_mode = fault_type
        self.fault_steps_remaining = duration_steps
        self.drift_offset = 0.0
        if fault_type == "frozen_sensor":
            self._frozen_values = None  # Will be set on next generate

    def generate_normal(self, ts: datetime) -> Dict[str, Any]:
        """Generate realistic normal sensor values."""
        hour = ts.hour + ts.minute / 60.0
        b = self.baseline

        # Diurnal temperature cycle (peak ~14:00)
        temp_cycle = b["temp_diurnal"] * math.sin((hour - 6) * math.pi / 12)
        temp = b["temp"] + temp_cycle + random.gauss(0, 0.4)

        # Pressure: slight diurnal wave + noise
        pressure_cycle = 2.5 * math.sin((hour - 10) * math.pi / 12)
        pressure = b["pressure"] + pressure_cycle + random.gauss(0, 0.3)

        # Humidity: inversely related to temperature roughly
        humidity_cycle = -15 * math.sin((hour - 6) * math.pi / 12)
        humidity = b["humidity"] + humidity_cycle + random.gauss(0, 1.5)
        humidity = max(10.0, min(100.0, humidity))

        return {
            "temperature": round(temp, 2),
            "pressure": round(pressure, 2),
            "humidity": round(humidity, 2),
        }

    def generate(self, ts: datetime) -> Dict[str, Any]:
        """Generate reading, applying fault if active."""
        self.step += 1
        normal = self.generate_normal(ts)

        if self.fault_mode and self.fault_steps_remaining > 0:
            self.fault_steps_remaining -= 1
            result = self._apply_fault(normal, ts)
            if self.fault_steps_remaining == 0:
                self.fault_mode = None
                self.drift_offset = 0.0
                self._frozen_values = None
            return result

        return normal

    def _apply_fault(self, normal: Dict, ts: datetime) -> Dict:
        data = dict(normal)

        if self.fault_mode == "temperature_spike":
            data["temperature"] = round(normal["temperature"] + random.uniform(20, 40), 2)

        elif self.fault_mode == "pressure_spike":
            data["pressure"] = round(normal["pressure"] + random.uniform(30, 60), 2)

        elif self.fault_mode == "humidity_spike":
            data["humidity"] = round(min(100, normal["humidity"] + random.uniform(20, 35)), 2)

        elif self.fault_mode == "frozen_sensor":
            if self._frozen_values is None:
                self._frozen_values = {k: v + random.gauss(0, 0.005) for k, v in normal.items()}
            data = {k: round(v, 3) for k, v in self._frozen_values.items()}

        elif self.fault_mode == "drift":
            self.drift_offset += 1.2
            data["temperature"] = round(normal["temperature"] + self.drift_offset, 2)

        elif self.fault_mode == "communication_failure":
            return {"temperature": None, "pressure": None, "humidity": None, "is_missing": True}

        elif self.fault_mode == "weather_event":
            # Coordinated changes across all sensors
            event_mag = random.uniform(3, 6)
            data["temperature"] = round(normal["temperature"] - event_mag, 2)
            data["pressure"] = round(normal["pressure"] - random.uniform(5, 15), 2)
            data["humidity"] = round(min(100, normal["humidity"] + random.uniform(15, 30)), 2)

        elif self.fault_mode == "multivariate_inconsistency":
            # Physically contradictory readings: acute humidity surge (+40%) with simultaneous sharp temperature rise (+18°C)
            data["temperature"] = round(normal["temperature"] + random.uniform(15, 25), 2)
            data["pressure"] = round(normal["pressure"] + random.uniform(25, 45), 2)
            data["humidity"] = round(min(100, normal["humidity"] + random.uniform(30, 45)), 2)

        return data


class SimulationService:
    """Orchestrates the simulation across all stations."""

    def __init__(self):
        self.simulators: Dict[str, StationSimulator] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.analyzer = SkyGuardAnalyzer(settings.MODEL_PATH)
        self.health_engine = SensorHealthEngine()

    async def initialize(self):
        """Seed stations in DB and create simulators."""
        async with AsyncSessionLocal() as db:
            for s_def in STATIONS:
                await station_service.upsert_station(db, {
                    "id": s_def["id"],
                    "name": s_def["name"],
                    "latitude": s_def["latitude"],
                    "longitude": s_def["longitude"],
                    "elevation": s_def["elevation"],
                    "location_desc": s_def["location_desc"],
                    "is_active": True,
                })
                self.simulators[s_def["id"]] = StationSimulator(s_def["id"])
        logger.info(f"Initialized {len(STATIONS)} stations")

        # Pre-populate with historical data only if database is empty
        async with AsyncSessionLocal() as db:
            existing = await station_service.get_recent_readings(db, "AWS-001", limit=1)
            if existing:
                logger.info("Database already populated with readings; skipping historical seeding.")
                return

        await self._seed_historical_data()

    async def _seed_historical_data(self, hours: int = 48):
        """Generate 48h of historical data for model training."""
        logger.info(f"Seeding {hours}h of historical data...")
        now = datetime.utcnow()
        start = now - timedelta(hours=hours)
        interval = timedelta(minutes=10)

        all_records = []
        async with AsyncSessionLocal() as db:
            for station_id, sim in self.simulators.items():
                ts = start
                records_for_training = []
                while ts < now:
                    data = sim.generate_normal(ts)
                    reading_data = {
                        "station_id": station_id,
                        "timestamp": ts,
                        "temperature": data.get("temperature"),
                        "pressure": data.get("pressure"),
                        "humidity": data.get("humidity"),
                        "is_missing": False,
                        "data_quality": "OK",
                    }
                    await station_service.add_reading(db, reading_data)
                    records_for_training.append({
                        "station_id": station_id,
                        "timestamp": ts.isoformat(),
                        **data
                    })
                    ts += interval
                all_records.extend(records_for_training)

        # Train model on AWS-001 data (primary station)
        aws001_records = [r for r in all_records if r["station_id"] == "AWS-001"]
        if len(aws001_records) >= 100:
            logger.info(f"Training model on {len(aws001_records)} records from AWS-001")
            success = self.analyzer.train(aws001_records, "AWS-001")
            if success:
                logger.info("Model trained successfully")

    def start(self):
        """Start the live simulation loop."""
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._simulation_loop())
            logger.info("Simulation started")

    def stop(self):
        """Stop the simulation loop."""
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("Simulation stopped")

    def inject_fault(self, station_id: str, fault_type: str, duration: int = 10):
        """Inject a fault into a specific station."""
        if station_id in self.simulators:
            self.simulators[station_id].set_fault(fault_type, duration)
            logger.info(f"Injected {fault_type} fault into {station_id} for {duration} steps")

    async def _simulation_loop(self):
        """Main simulation loop: generate readings and run analysis."""
        while self.is_running:
            try:
                await self._tick()
                await asyncio.sleep(settings.SIM_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                await asyncio.sleep(5)

    async def _tick(self):
        """Generate one reading per station and analyze."""
        now = datetime.utcnow()
        async with AsyncSessionLocal() as db:
            for station_id, sim in self.simulators.items():
                try:
                    data = sim.generate(now)
                    is_missing = data.pop("is_missing", False)

                    reading_data = {
                        "station_id": station_id,
                        "timestamp": now,
                        "temperature": data.get("temperature"),
                        "pressure": data.get("pressure"),
                        "humidity": data.get("humidity"),
                        "is_missing": is_missing,
                        "data_quality": "OK" if not is_missing else "FAILED",
                    }
                    reading = await station_service.add_reading(db, reading_data)

                    # Analyze
                    recent = await station_service.get_recent_readings(db, station_id, limit=60)
                    recent_records = [{
                        "station_id": r.station_id,
                        "timestamp": r.timestamp.isoformat(),
                        "temperature": r.temperature,
                        "pressure": r.pressure,
                        "humidity": r.humidity,
                        "is_missing": r.is_missing,
                    } for r in recent]

                    latest_record = {
                        "station_id": station_id,
                        "timestamp": now.isoformat(),
                        "is_missing": is_missing,
                        **data
                    }

                    analysis = self.analyzer.analyze_reading(recent_records, station_id, latest_record)

                    # Save anomaly record
                    anomaly_data = {
                        "station_id": station_id,
                        "reading_id": reading.id,
                        "timestamp": now,
                        "anomaly_score": analysis["anomaly_score"],
                        "is_anomaly": analysis["is_anomaly"],
                        "classification": analysis["classification"],
                        "confidence": analysis["confidence"],
                        "affected_sensor": analysis.get("affected_sensor"),
                        "fault_type": analysis.get("fault_type"),
                        "observed_temperature": data.get("temperature"),
                        "expected_temperature": analysis.get("expected_temperature"),
                        "observed_pressure": data.get("pressure"),
                        "expected_pressure": analysis.get("expected_pressure"),
                        "observed_humidity": data.get("humidity"),
                        "expected_humidity": analysis.get("expected_humidity"),
                        "reason": analysis.get("reason"),
                        "evidence": json.dumps(analysis.get("evidence", {})),
                        "probable_cause": analysis.get("probable_cause"),
                        "recommended_action": analysis.get("recommended_action"),
                    }
                    anomaly = await station_service.save_anomaly(db, anomaly_data)

                    # Create alert if genuine hardware/telemetry fault is significant (deduplicating open alerts)
                    HARDWARE_FAULT_CLASSIFICATIONS = {
                        "PROBABLE_SENSOR_ANOMALY",
                        "PROBABLE_SENSOR_FAULT",
                        "POSSIBLE_COMMUNICATION_FAILURE",
                        "POSSIBLE_DATA_QUALITY_ISSUE"
                    }
                    classification = analysis["classification"]
                    affected = analysis.get("affected_sensor")

                    if classification in HARDWARE_FAULT_CLASSIFICATIONS and analysis["anomaly_score"] > 0.4:
                        severity = "CRITICAL" if analysis["anomaly_score"] > 0.7 else "WARNING"
                        existing_alert = await station_service.get_open_alert(db, station_id, affected)
                        if not existing_alert:
                            alert_data = {
                                "station_id": station_id,
                                "anomaly_id": anomaly.id,
                                "timestamp": now,
                                "severity": severity,
                                "sensor": affected or "sensor",
                                "title": f"{classification.replace('_', ' ').title()} — {station_id}",
                                "message": analysis.get("reason", "Anomalous reading detected."),
                                "probable_cause": analysis.get("probable_cause"),
                                "confidence": analysis.get("confidence"),
                                "recommended_action": analysis.get("recommended_action"),
                                "status": "OPEN",
                            }
                            await station_service.save_alert(db, alert_data)
                    elif classification == "NORMAL":
                        # Auto-resolve open alerts for this station as telemetry returned to normal
                        await station_service.resolve_alerts_for_sensor(db, station_id)

                    # Update health: Only hardware/sensor faults degrade sensor health
                    all_anomalies = await station_service.get_station_anomalies(db, station_id, limit=50)
                    hardware_anomalies_list = [
                        a for a in all_anomalies
                        if a.is_anomaly and a.classification in HARDWARE_FAULT_CLASSIFICATIONS
                    ]
                    all_readings = await station_service.get_recent_readings(db, station_id, limit=50)
                    missing_count = sum(1 for r in all_readings if r.is_missing)
                    existing_health_records = await station_service.get_station_health(db, station_id)

                    sensor_health_states = {}
                    for sensor in ["temperature", "pressure", "humidity"]:
                        sensor_anomalies = [a for a in hardware_anomalies_list if a.affected_sensor == sensor]
                        prev_h = next((h for h in existing_health_records if h.sensor_type == sensor), None)
                        prev_score = prev_h.health_score if prev_h else None

                        health_state = self.health_engine.update_health(
                            sensor=sensor,
                            recent_anomalies=sensor_anomalies,
                            total_readings=len(all_readings),
                            missing_readings=missing_count,
                            fault_history_count=len(sensor_anomalies),
                            previous_health_score=prev_score
                        )
                        sensor_health_states[sensor] = health_state
                        await station_service.upsert_health(db, station_id, sensor, {
                            "health_score": health_state.health_score,
                            "status": health_state.status,
                            "degradation_trend": health_state.degradation_trend,
                            "maintenance_status": health_state.maintenance_status,
                            "maintenance_recommendation": health_state.maintenance_recommendation,
                            "maintenance_reasons": json.dumps(health_state.maintenance_reasons),
                            "recent_anomaly_count": health_state.recent_anomaly_count,
                            "missing_data_rate": health_state.missing_data_rate,
                            "consistency_score": health_state.consistency_score,
                            "fault_history_count": health_state.fault_history_count,
                        })

                    # Compute overall health consistently from underlying sensors
                    worst_sensor = min(sensor_health_states.values(), key=lambda s: s.health_score)
                    overall_score = round(worst_sensor.health_score, 1)
                    overall_status = worst_sensor.status
                    overall_trend = "DECLINING" if any(s.degradation_trend == "DECLINING" for s in sensor_health_states.values()) else "STABLE"
                    overall_maint_status = worst_sensor.maintenance_status
                    overall_rec = worst_sensor.maintenance_recommendation if worst_sensor.health_score < 85.0 else "Nominal operations across all station sensors. Routine monitoring."

                    overall_reasons = []
                    for s in sensor_health_states.values():
                        if s.health_score < 85.0:
                            overall_reasons.extend([f"[{s.sensor.upper()}] {r}" for r in s.maintenance_reasons if "baseline" not in r.lower()])
                    if not overall_reasons:
                        overall_reasons = ["All station telemetry sensors operate strictly within learned baseline parameters"]

                    await station_service.upsert_health(db, station_id, "overall", {
                        "health_score": overall_score,
                        "status": overall_status,
                        "degradation_trend": overall_trend,
                        "maintenance_status": overall_maint_status,
                        "maintenance_recommendation": overall_rec,
                        "maintenance_reasons": json.dumps(overall_reasons),
                        "recent_anomaly_count": sum(s.recent_anomaly_count for s in sensor_health_states.values()),
                        "missing_data_rate": max(s.missing_data_rate for s in sensor_health_states.values()),
                        "consistency_score": round(sum(s.consistency_score for s in sensor_health_states.values()) / 3.0, 3),
                        "fault_history_count": sum(s.fault_history_count for s in sensor_health_states.values()),
                    })

                except Exception as e:
                    logger.error(f"Error processing station {station_id}: {e}", exc_info=True)

_sim_service_instance: Optional[SimulationService] = None

def get_sim_service() -> Optional[SimulationService]:
    global _sim_service_instance
    return _sim_service_instance

def set_sim_service(instance: SimulationService):
    global _sim_service_instance
    _sim_service_instance = instance
