"""
SkyGuard AI — NOAA ASOS 5-Minute Data Adapter
==============================================
Official Data Source:
  NOAA / NCEI — 5-Minute Surface Weather Observations
  from the Automated Surface Observing Systems (ASOS) Network
  Dataset Identifier: gov.noaa.ncdc:C00418
  NCEI DSI: 6401_02
  Metadata URL: https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc%3AC00418/html
  Access Archive: https://www.ncei.noaa.gov/pub/data/asos-fivemin/

This adapter reads, parses, validates, and imports real NOAA ASOS observations
into the existing SkyGuard AI architecture without modifying or deleting existing
simulation stations, database schemas, or ML pipelines.
"""

import os
import re
import math
import json
import logging
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.db_models import Station, SensorReading, SensorHealth

logger = logging.getLogger(__name__)

NOAA_DATASET_ID = "gov.noaa.ncdc:C00418"
NOAA_DSI = "6401_02"
NOAA_SOURCE_TAG = "NOAA_ASOS"
NOAA_SOURCE_URL = "https://www.ncei.noaa.gov/pub/data/asos-fivemin/"
NOAA_METADATA_URL = "https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc%3AC00418/html"

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "noaa_asos")

NOAA_ASOS_STATIONS: Dict[str, Dict[str, Any]] = {
    "KJFK": {
        "wban": "94789",
        "name": "NEW YORK JFK INTL AP",
        "latitude": 40.639,
        "longitude": -73.762,
        "elevation": 6.7,
        "state": "NY",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 94789 | New York JFK International Airport, NY, US",
    },
    "KORD": {
        "wban": "94846",
        "name": "CHICAGO OHARE INTL AP",
        "latitude": 41.995,
        "longitude": -87.934,
        "elevation": 205.4,
        "state": "IL",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 94846 | Chicago O'Hare International Airport, IL, US",
    },
    "KLAX": {
        "wban": "23174",
        "name": "LOS ANGELES MUNICIPAL ARPT",
        "latitude": 33.938,
        "longitude": -118.389,
        "elevation": 99.4,
        "state": "CA",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 23174 | Los Angeles International Airport, CA, US",
    },
    "KATL": {
        "wban": "13874",
        "name": "ATLANTA HARTSFIELD INTL AP",
        "latitude": 33.630,
        "longitude": -84.442,
        "elevation": 312.7,
        "state": "GA",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 13874 | Atlanta Hartsfield-Jackson Airport, GA, US",
    },
    "KDEN": {
        "wban": "03017",
        "name": "DENVER INTERNATIONAL AIRPORT",
        "latitude": 39.847,
        "longitude": -104.656,
        "elevation": 1647.2,
        "state": "CO",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 03017 | Denver International Airport, CO, US",
    },
    "KDFW": {
        "wban": "03927",
        "name": "DALLAS-FORT WORTH INTL AP",
        "latitude": 32.898,
        "longitude": -97.019,
        "elevation": 181.7,
        "state": "TX",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 03927 | Dallas-Fort Worth International Airport, TX, US",
    },
    "KSFO": {
        "wban": "23234",
        "name": "SAN FRANCISCO INTL AP",
        "latitude": 37.620,
        "longitude": -122.365,
        "elevation": 5.5,
        "state": "CA",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 23234 | San Francisco International Airport, CA, US",
    },
    "KBOS": {
        "wban": "14739",
        "name": "GEN E L LOGAN INTERNATIONAL AIRPORT",
        "latitude": 42.361,
        "longitude": -71.010,
        "elevation": 3.3,
        "state": "MA",
        "country": "US",
        "source": NOAA_SOURCE_TAG,
        "location_desc": f"Source: {NOAA_SOURCE_TAG} | WBAN 14739 | Boston Logan International Airport, MA, US",
    },
}


class NOAAASOSAdapter:
    """
    Adapter for downloading, parsing, and ingesting official NOAA ASOS
    5-minute surface observations (dataset gov.noaa.ncdc:C00418 / DSI 6401_02).
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_raw_filepath(self, station_id: str, year_month: str = "202201") -> str:
        return os.path.join(self.cache_dir, f"64010{station_id}{year_month}.dat")

    def fetch_raw_file(self, station_id: str, year_month: str = "202201") -> str:
        filepath = self.get_raw_filepath(station_id, year_month)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 50000:
            return filepath

        year = year_month[:4]
        filename = f"64010{station_id}{year_month}.dat"
        url = f"{NOAA_SOURCE_URL}6401-{year}/{filename}"
        logger.info(f"Downloading real NOAA ASOS data for {station_id} from {url}...")

        req = urllib.request.Request(url, headers={"User-Agent": "SkyGuard-AI-Adapter/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            with open(filepath, "wb") as f:
                f.write(content)
        return filepath

    @staticmethod
    def parse_noaa_line(line: str) -> Optional[Dict[str, Any]]:
        if not line or "5-MIN" not in line:
            return None

        try:
            parts = line.split("5-MIN", 1)
            prefix, body = parts[0], parts[1]

            m_date = re.search(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})", prefix)
            if not m_date:
                return None
            year, month, day, hour_lst, min_lst = map(int, m_date.groups())

            m_utc = re.search(r"\b(\d{2})(\d{2})(\d{2})Z\b", body)
            if m_utc:
                utc_day, utc_hour, utc_min = map(int, m_utc.groups())
                try:
                    ts = datetime(year, month, utc_day, utc_hour, utc_min)
                except Exception:
                    ts = datetime(year, month, day, hour_lst, min_lst)
            else:
                ts = datetime(year, month, day, hour_lst, min_lst)

            temp_c: Optional[float] = None
            dew_c: Optional[float] = None

            # High precision 0.1C remarks T-group
            m_t = re.search(r"\bT([01])(\d{3})([01])(\d{3})\b", body)
            if m_t:
                s_t, v_t, s_d, v_d = m_t.groups()
                temp_c = (float(v_t) / 10.0) * (-1.0 if s_t == "1" else 1.0)
                dew_c = (float(v_d) / 10.0) * (-1.0 if s_d == "1" else 1.0)
            else:
                # Standard METAR temp/dew field e.g. 09/08 or M13/M15
                m_metar_t = re.search(r"\b(M?\d{2})/(M?\d{2})\b", body)
                if m_metar_t:
                    t_str, d_str = m_metar_t.groups()
                    temp_c = -float(t_str[1:]) if t_str.startswith("M") else float(t_str)
                    dew_c = -float(d_str[1:]) if d_str.startswith("M") else float(d_str)

            if temp_c is not None and (temp_c < -65.0 or temp_c > 60.0):
                temp_c = None
            if dew_c is not None and (dew_c < -65.0 or dew_c > 50.0):
                dew_c = None

            pres_hpa: Optional[float] = None
            m_a = re.search(r"\bA(\d{4})\b", body)
            if m_a:
                inhg = float(m_a.group(1)) / 100.0
                if 25.0 <= inhg <= 33.0:
                    pres_hpa = round(inhg * 33.8639, 2)

            rh: Optional[float] = None
            if temp_c is not None and dew_c is not None:
                try:
                    a, b = 17.625, 243.04
                    alpha = (a * temp_c) / (b + temp_c)
                    beta = (a * dew_c) / (b + dew_c)
                    computed_rh = 100.0 * math.exp(beta - alpha)
                    rh = round(min(100.0, max(1.0, computed_rh)), 1)
                except Exception:
                    rh = None

            if rh is None:
                m_rh = re.search(r"\b([1-9]\d|100)\b", body)
                if m_rh:
                    val = float(m_rh.group(1))
                    if 1.0 <= val <= 100.0:
                        rh = val

            is_missing = (temp_c is None and pres_hpa is None and rh is None)
            if is_missing:
                data_quality = "NOAA_ASOS_MISSING"
            elif None in (temp_c, pres_hpa, rh):
                data_quality = "NOAA_ASOS_PARTIAL"
            else:
                data_quality = "NOAA_ASOS"

            return {
                "timestamp": ts,
                "temperature": temp_c,
                "pressure": pres_hpa,
                "humidity": rh,
                "is_missing": is_missing,
                "data_quality": data_quality,
                "raw_data": json.dumps({
                    "source": NOAA_SOURCE_TAG,
                    "dataset": NOAA_DATASET_ID,
                    "dsi": NOAA_DSI,
                    "raw_line": line.strip()[:200]
                })
            }
        except Exception as e:
            return None

    def parse_station_file(
        self,
        station_id: str,
        start_date: datetime,
        end_date: datetime,
        year_month: str = "202201"
    ) -> List[Dict[str, Any]]:
        filepath = self.fetch_raw_file(station_id, year_month)
        records = []
        seen_timestamps = set()

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parsed = self.parse_noaa_line(line)
                if parsed:
                    ts = parsed["timestamp"]
                    if start_date <= ts <= end_date:
                        if ts not in seen_timestamps:
                            seen_timestamps.add(ts)
                            parsed["station_id"] = station_id
                            records.append(parsed)

        records.sort(key=lambda r: r["timestamp"])
        return records

    async def import_stations_and_readings(
        self,
        db: AsyncSession,
        station_ids: Optional[List[str]] = None,
        days: int = 7,
        start_day: int = 1,
        year_month: str = "202201"
    ) -> Dict[str, Any]:
        target_stations = station_ids or list(NOAA_ASOS_STATIONS.keys())
        year = int(year_month[:4])
        month = int(year_month[4:6])

        start_date = datetime(year, month, start_day, 0, 0, 0)
        end_date = start_date + timedelta(days=days) - timedelta(minutes=5)

        logger.info(f"Starting NOAA ASOS import for {len(target_stations)} stations from {start_date} to {end_date}")

        import_summary = {
            "source": NOAA_SOURCE_TAG,
            "dataset_id": NOAA_DATASET_ID,
            "dsi": NOAA_DSI,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "stations_imported": [],
            "total_observations": 0,
            "missing_stats": {
                "temperature_missing": 0,
                "pressure_missing": 0,
                "humidity_missing": 0,
                "total_missing_records": 0
            }
        }

        for st_id in target_stations:
            if st_id not in NOAA_ASOS_STATIONS:
                continue

            meta = NOAA_ASOS_STATIONS[st_id]

            # 1. Upsert Station record
            st_result = await db.execute(select(Station).where(Station.id == st_id))
            existing_station = st_result.scalar_one_or_none()

            if existing_station:
                existing_station.name = meta["name"]
                existing_station.latitude = meta["latitude"]
                existing_station.longitude = meta["longitude"]
                existing_station.elevation = meta["elevation"]
                existing_station.location_desc = meta["location_desc"]
                existing_station.is_active = True
            else:
                new_station = Station(
                    id=st_id,
                    name=meta["name"],
                    latitude=meta["latitude"],
                    longitude=meta["longitude"],
                    elevation=meta["elevation"],
                    location_desc=meta["location_desc"],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(new_station)

            await db.commit()

            # 2. Parse observations
            records = self.parse_station_file(st_id, start_date, end_date, year_month)

            # 3. Check for existing readings in date range to avoid duplicate inserts
            existing_ts_query = await db.execute(
                select(SensorReading.timestamp).where(
                    SensorReading.station_id == st_id,
                    SensorReading.timestamp >= start_date,
                    SensorReading.timestamp <= end_date
                )
            )
            existing_timestamps = set(r[0] for r in existing_ts_query.fetchall())

            readings_to_insert = []
            st_temp_missing = 0
            st_pres_missing = 0
            st_hum_missing = 0

            for r in records:
                if r["temperature"] is None:
                    st_temp_missing += 1
                if r["pressure"] is None:
                    st_pres_missing += 1
                if r["humidity"] is None:
                    st_hum_missing += 1

                if r["timestamp"] not in existing_timestamps:
                    readings_to_insert.append(
                        SensorReading(
                            station_id=st_id,
                            timestamp=r["timestamp"],
                            temperature=r["temperature"],
                            pressure=r["pressure"],
                            humidity=r["humidity"],
                            is_missing=r["is_missing"],
                            data_quality=r["data_quality"],
                            raw_data=r["raw_data"]
                        )
                    )

            batch_size = 500
            for i in range(0, len(readings_to_insert), batch_size):
                batch = readings_to_insert[i:i + batch_size]
                db.add_all(batch)
                await db.commit()

            # 4. Upsert nominal SensorHealth for real NOAA stations
            now_utc = datetime.utcnow()
            for sensor_type in ["temperature", "pressure", "humidity", "overall"]:
                h_res = await db.execute(
                    select(SensorHealth).where(
                        SensorHealth.station_id == st_id,
                        SensorHealth.sensor_type == sensor_type
                    )
                )
                existing_h = h_res.scalar_one_or_none()
                rec_desc = f"NOAA ASOS operational feed active for {sensor_type}. Real physical telemetry."
                if existing_h:
                    existing_h.health_score = 100.0
                    existing_h.status = "HEALTHY"
                    existing_h.degradation_trend = "STABLE"
                    existing_h.maintenance_status = "NOMINAL_MONITORING"
                    existing_h.maintenance_recommendation = rec_desc
                    existing_h.timestamp = now_utc
                else:
                    db.add(
                        SensorHealth(
                            station_id=st_id,
                            sensor_type=sensor_type,
                            timestamp=now_utc,
                            health_score=100.0,
                            status="HEALTHY",
                            degradation_trend="STABLE",
                            maintenance_status="NOMINAL_MONITORING",
                            maintenance_recommendation=rec_desc,
                            recent_anomaly_count=0,
                            missing_data_rate=round(st_temp_missing / max(1, len(records)), 3),
                            consistency_score=1.0,
                            fault_history_count=0
                        )
                    )
            await db.commit()

            st_summary = {
                "station_id": st_id,
                "name": meta["name"],
                "state": meta["state"],
                "latitude": meta["latitude"],
                "longitude": meta["longitude"],
                "elevation_m": meta["elevation"],
                "observations_count": len(records),
                "newly_inserted": len(readings_to_insert),
                "missing_values": {
                    "temperature": st_temp_missing,
                    "pressure": st_pres_missing,
                    "humidity": st_hum_missing
                }
            }
            import_summary["stations_imported"].append(st_summary)
            import_summary["total_observations"] += len(records)
            import_summary["missing_stats"]["temperature_missing"] += st_temp_missing
            import_summary["missing_stats"]["pressure_missing"] += st_pres_missing
            import_summary["missing_stats"]["humidity_missing"] += st_hum_missing

        return import_summary


_adapter_instance: Optional[NOAAASOSAdapter] = None

def get_noaa_adapter() -> NOAAASOSAdapter:
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = NOAAASOSAdapter()
    return _adapter_instance
