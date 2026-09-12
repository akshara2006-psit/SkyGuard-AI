from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.connection import Base

class Station(Base):
    __tablename__ = "stations"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation = Column(Float, nullable=True)
    location_desc = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    readings = relationship("SensorReading", back_populates="station", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="station", cascade="all, delete-orphan")
    health_records = relationship("SensorHealth", back_populates="station", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="station", cascade="all, delete-orphan")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String, ForeignKey("stations.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    is_missing = Column(Boolean, default=False)
    data_quality = Column(String, default="OK")
    raw_data = Column(Text, nullable=True)
    station = relationship("Station", back_populates="readings")
    __table_args__ = (
        Index("ix_readings_station_ts", "station_id", "timestamp"),
        Index("ix_readings_ts", "timestamp"),
    )

class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String, ForeignKey("stations.id"), nullable=False)
    reading_id = Column(Integer, ForeignKey("sensor_readings.id"), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, default=False)
    classification = Column(String, default="NORMAL")
    confidence = Column(Float, nullable=True)
    affected_sensor = Column(String, nullable=True)
    observed_temperature = Column(Float, nullable=True)
    expected_temperature = Column(Float, nullable=True)
    observed_pressure = Column(Float, nullable=True)
    expected_pressure = Column(Float, nullable=True)
    observed_humidity = Column(Float, nullable=True)
    expected_humidity = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    probable_cause = Column(String, nullable=True)
    recommended_action = Column(String, nullable=True)
    fault_type = Column(String, nullable=True)
    station = relationship("Station", back_populates="anomalies")
    __table_args__ = (
        Index("ix_anomalies_station_ts", "station_id", "timestamp"),
        Index("ix_anomalies_ts", "timestamp"),
    )

class SensorHealth(Base):
    __tablename__ = "sensor_health"
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String, ForeignKey("stations.id"), nullable=False)
    sensor_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    health_score = Column(Float, default=100.0)
    recent_anomaly_count = Column(Integer, default=0)
    missing_data_rate = Column(Float, default=0.0)
    consistency_score = Column(Float, default=1.0)
    fault_history_count = Column(Integer, default=0)
    status = Column(String, default="HEALTHY")
    degradation_trend = Column(String, default="STABLE")
    maintenance_status = Column(String, default="NOMINAL_MONITORING")
    maintenance_recommendation = Column(Text, nullable=True)
    maintenance_reasons = Column(Text, nullable=True)
    station = relationship("Station", back_populates="health_records")
    __table_args__ = (Index("ix_health_station_sensor", "station_id", "sensor_type"),)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String, ForeignKey("stations.id"), nullable=False)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(String, nullable=False)
    sensor = Column(String, nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    probable_cause = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    recommended_action = Column(String, nullable=True)
    status = Column(String, default="OPEN")
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    station = relationship("Station", back_populates="alerts")
    __table_args__ = (
        Index("ix_alerts_station_ts", "station_id", "timestamp"),
        Index("ix_alerts_status", "status"),
    )
