"""
SkyGuard AI - FastAPI Route & Endpoint Unit Tests
"""
import pytest
import os
import sys
import asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.main import app
from app.database.connection import init_db, close_db
from app.services.simulation_service import get_sim_service

async def run_all():
    print("Initializing Database tables...")
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("Testing Root Endpoint (/)...")
        res = await ac.get("/")
        assert res.status_code == 200
        assert res.json()["name"] == "SkyGuard AI"

        print("Testing Health Endpoint (/health)...")
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        print("Testing Summary Endpoint (/api/summary)...")
        res = await ac.get("/api/summary")
        assert res.status_code == 200
        assert "total_stations" in res.json()

        print("Testing Real-Time Analyze Endpoint (/api/analyze)...")
        payload = {
            "station_id": "AWS-001",
            "timestamp": "2026-08-30T12:00:00",
            "temperature": 68.5,
            "pressure": 1005.0,
            "humidity": 65.0
        }
        res = await ac.post("/api/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "anomaly_score" in data
        assert "confidence" in data
        assert "classification" in data
        assert "reason" in data
        print(f"Analyze Output: Classification='{data['classification']}', Score={data['anomaly_score_pct']}%, Confidence={data['confidence_pct']}%")

        print("Testing Simulation Status Endpoint (/api/simulation/status)...")
        res = await ac.get("/api/simulation/status")
        assert res.status_code == 200

    # Clean up background simulation service if created
    svc = get_sim_service()
    if svc:
        svc.stop()

    # Clean up database connections to prevent hanging worker threads
    await close_db()

    print("\nAll FastAPI endpoints verified and working perfectly!")

if __name__ == "__main__":
    asyncio.run(run_all())
    sys.exit(0)
