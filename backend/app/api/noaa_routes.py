"""
SkyGuard AI — NOAA ASOS API Routes
==================================
Endpoints for inspecting real NOAA ASOS stations, metadata,
and triggering/querying the real-data adapter layer.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from ..database.connection import get_db
from ..adapters.noaa_asos_adapter import (
    get_noaa_adapter,
    NOAA_ASOS_STATIONS,
    NOAA_DATASET_ID,
    NOAA_DSI,
    NOAA_SOURCE_TAG,
    NOAA_SOURCE_URL,
    NOAA_METADATA_URL,
)
from ..models.db_models import Station, SensorReading
from sqlalchemy import select, func

noaa_router = APIRouter(prefix="/noaa", tags=["NOAA ASOS Real Data"])


@noaa_router.get("/status")
async def get_noaa_status(db: AsyncSession = Depends(get_db)):
    """
    Returns the real NOAA ASOS data integration status,
    official metadata provenance, station count, observation totals,
    and missing value statistics from the database.
    """
    # Count real NOAA stations in DB
    stations_q = await db.execute(
        select(Station).where(Station.id.in_(list(NOAA_ASOS_STATIONS.keys())))
    )
    imported_stations = stations_q.scalars().all()
    st_ids = [s.id for s in imported_stations]

    total_obs = 0
    date_range = {"min": None, "max": None}
    missing_stats = {"temperature_missing": 0, "pressure_missing": 0, "humidity_missing": 0}

    if st_ids:
        # Total count
        cnt_q = await db.execute(
            select(func.count(SensorReading.id)).where(SensorReading.station_id.in_(st_ids))
        )
        total_obs = cnt_q.scalar() or 0

        # Min and Max timestamp
        min_max_q = await db.execute(
            select(
                func.min(SensorReading.timestamp),
                func.max(SensorReading.timestamp)
            ).where(SensorReading.station_id.in_(st_ids))
        )
        min_ts, max_ts = min_max_q.fetchone() or (None, None)
        date_range = {
            "min": min_ts.isoformat() if min_ts else None,
            "max": max_ts.isoformat() if max_ts else None,
        }

        # Missing counts
        miss_q = await db.execute(
            select(
                func.count(SensorReading.id).filter(SensorReading.temperature.is_(None)),
                func.count(SensorReading.id).filter(SensorReading.pressure.is_(None)),
                func.count(SensorReading.id).filter(SensorReading.humidity.is_(None)),
            ).where(SensorReading.station_id.in_(st_ids))
        )
        t_m, p_m, h_m = miss_q.fetchone() or (0, 0, 0)
        missing_stats = {
            "temperature_missing": t_m,
            "pressure_missing": p_m,
            "humidity_missing": h_m,
            "total_missing_values": t_m + p_m + h_m
        }

    return {
        "status": "OPERATIONAL" if imported_stations else "READY_FOR_IMPORT",
        "official_source": {
            "name": "NOAA / NCEI 5-Minute Surface Weather Observations (ASOS)",
            "dataset_identifier": NOAA_DATASET_ID,
            "dsi_number": NOAA_DSI,
            "source_tag": NOAA_SOURCE_TAG,
            "archive_url": NOAA_SOURCE_URL,
            "metadata_url": NOAA_METADATA_URL,
        },
        "available_stations_count": len(NOAA_ASOS_STATIONS),
        "imported_stations_count": len(imported_stations),
        "imported_station_ids": st_ids,
        "total_observations": total_obs,
        "date_range": date_range,
        "missing_statistics": missing_stats,
    }


@noaa_router.get("/stations")
async def get_noaa_stations(db: AsyncSession = Depends(get_db)):
    """
    Returns list of official NOAA ASOS stations registered in SkyGuard,
    including their official NOAA metadata and live reading counts.
    """
    result = []
    for st_id, meta in NOAA_ASOS_STATIONS.items():
        # Query count in DB
        cnt_q = await db.execute(
            select(func.count(SensorReading.id)).where(SensorReading.station_id == st_id)
        )
        obs_count = cnt_q.scalar() or 0

        # Latest reading
        last_q = await db.execute(
            select(SensorReading).where(SensorReading.station_id == st_id)
            .order_by(SensorReading.timestamp.desc()).limit(1)
        )
        last_r = last_q.scalar_one_or_none()

        result.append({
            "station_id": st_id,
            "station_name": meta["name"],
            "wban": meta["wban"],
            "state": meta["state"],
            "country": meta["country"],
            "latitude": meta["latitude"],
            "longitude": meta["longitude"],
            "elevation": meta["elevation"],
            "source": meta["source"],
            "observations_count": obs_count,
            "last_reading": {
                "timestamp": last_r.timestamp.isoformat() if last_r else None,
                "temperature": last_r.temperature if last_r else None,
                "pressure": last_r.pressure if last_r else None,
                "humidity": last_r.humidity if last_r else None,
            } if last_r else None
        })

    return result


@noaa_router.post("/import")
async def import_noaa_data(
    days: int = Query(default=7, ge=1, le=30, description="Number of days to import (7-30 recommended)"),
    station_ids: Optional[str] = Query(default=None, description="Comma-separated station IDs, or empty for all 8"),
    db: AsyncSession = Depends(get_db)
):
    """
    Imports real NOAA ASOS observations into SkyGuard database.
    Does NOT modify or remove any existing demo stations.
    """
    adapter = get_noaa_adapter()
    st_list = [s.strip().upper() for s in station_ids.split(",")] if station_ids else None

    summary = await adapter.import_stations_and_readings(
        db=db,
        station_ids=st_list,
        days=days,
        start_day=1,
        year_month="202201"
    )
    return summary
