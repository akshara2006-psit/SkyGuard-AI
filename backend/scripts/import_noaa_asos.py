"""
SkyGuard AI — NOAA ASOS Ingestion CLI
======================================
Imports official NOAA ASOS 5-minute weather observations (DSI 6401_02)
into the SkyGuard AI database.

Usage:
  python backend/scripts/import_noaa_asos.py [--days 7] [--stations KJFK,KORD,KDEN]
"""

import sys
import os
import asyncio
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import AsyncSessionLocal
from app.adapters.noaa_asos_adapter import get_noaa_adapter, NOAA_ASOS_STATIONS


async def main():
    parser = argparse.ArgumentParser(description="Import real NOAA ASOS 5-minute data into SkyGuard AI")
    parser.add_argument("--days", type=int, default=7, help="Number of days to import (default: 7)")
    parser.add_argument("--stations", type=str, default=None, help="Comma-separated station IDs or None for all 8")
    parser.add_argument("--year-month", type=str, default="202201", help="YYYYMM archive month (default: 202201)")
    args = parser.parse_args()

    station_list = [s.strip().upper() for s in args.stations.split(",")] if args.stations else list(NOAA_ASOS_STATIONS.keys())

    print("=================================================================")
    print("SKYGUARD AI — NOAA ASOS 5-MINUTE DATA INGESTION")
    print("=================================================================")
    print(f"Target Stations ({len(station_list)}): {', '.join(station_list)}")
    print(f"Time Range: {args.days} days from start of {args.year_month}")
    print("Dataset: NOAA/NCEI ASOS 5-Minute Observations (gov.noaa.ncdc:C00418 / DSI 6401_02)")
    print("-----------------------------------------------------------------")

    adapter = get_noaa_adapter()
    async with AsyncSessionLocal() as db:
        summary = await adapter.import_stations_and_readings(
            db=db,
            station_ids=station_list,
            days=args.days,
            start_day=1,
            year_month=args.year_month
        )

    print("\n=== IMPORT COMPLETE ===")
    print(f"Total Real Observations Ingested: {summary['total_observations']}")
    print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
    print("\nStation Breakdown:")
    for st in summary["stations_imported"]:
        print(f"  * {st['station_id']} ({st['name']}, {st['state']}):")
        print(f"      Lat: {st['latitude']}, Lon: {st['longitude']}, Elev: {st['elevation_m']}m")
        print(f"      Observations: {st['observations_count']} (Newly inserted: {st['newly_inserted']})")
        print(f"      Missing: Temp={st['missing_values']['temperature']}, Pres={st['missing_values']['pressure']}, RH={st['missing_values']['humidity']}")

    m = summary["missing_stats"]
    tot = summary["total_observations"]
    print("\nMissing Values Summary:")
    print(f"  * Temperature missing: {m['temperature_missing']} ({m['temperature_missing']/max(1, tot)*100:.2f}%)")
    print(f"  * Pressure missing:    {m['pressure_missing']} ({m['pressure_missing']/max(1, tot)*100:.2f}%)")
    print(f"  * Humidity missing:    {m['humidity_missing']} ({m['humidity_missing']/max(1, tot)*100:.2f}%)")
    print("=================================================================")


if __name__ == "__main__":
    asyncio.run(main())
