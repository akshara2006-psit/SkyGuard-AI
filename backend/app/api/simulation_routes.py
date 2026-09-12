"""
SkyGuard AI - Simulation API Routes
Endpoints for controlling the live simulation and demo fault scenarios.
"""
from fastapi import APIRouter
from ..services.simulation_service import get_sim_service
import logging

logger = logging.getLogger(__name__)
sim_router = APIRouter()

@sim_router.get("/simulation/status")
async def simulation_status():
    svc = get_sim_service()
    if svc is None:
        return {"running": False, "stations": []}
    return {
        "running": svc.is_running,
        "stations": list(svc.simulators.keys())
    }

@sim_router.post("/simulation/start")
async def start_simulation():
    svc = get_sim_service()
    if svc is None:
        return {"error": "Simulation service not initialized"}
    svc.start()
    return {"status": "started", "running": True}

@sim_router.post("/simulation/stop")
async def stop_simulation():
    svc = get_sim_service()
    if svc is None:
        return {"error": "Simulation service not initialized"}
    svc.stop()
    return {"status": "stopped", "running": False}

@sim_router.post("/simulation/inject")
async def inject_fault(payload: dict):
    svc = get_sim_service()
    if svc is None:
        return {"error": "Simulation service not initialized"}
    station_id = payload.get("station_id", "AWS-001")
    fault_type = payload.get("fault_type", "temperature_spike")
    duration = int(payload.get("duration", 10))

    svc.inject_fault(station_id, fault_type, duration)
    return {
        "status": "injected",
        "station_id": station_id,
        "fault_type": fault_type,
        "duration_steps": duration
    }

@sim_router.post("/simulation/scenario/{scenario_name}")
async def run_scenario(scenario_name: str):
    svc = get_sim_service()
    if svc is None:
        return {"error": "Simulation service not initialized"}

    scenarios = {
        "normal": {},
        "temperature_spike": {"station_id": "AWS-001", "fault_type": "temperature_spike", "duration": 8},
        "frozen_humidity": {"station_id": "AWS-002", "fault_type": "frozen_sensor", "duration": 12},
        "sensor_drift": {"station_id": "AWS-003", "fault_type": "drift", "duration": 15},
        "comm_failure": {"station_id": "AWS-004", "fault_type": "communication_failure", "duration": 6},
        "weather_event": {"station_id": "AWS-005", "fault_type": "weather_event", "duration": 8},
        "multivariate_inconsistency": {"station_id": "AWS-006", "fault_type": "multivariate_inconsistency", "duration": 8},
        "pressure_spike": {"station_id": "AWS-006", "fault_type": "pressure_spike", "duration": 6},
    }

    if scenario_name not in scenarios:
        return {"error": f"Unknown scenario: {scenario_name}. Valid: {list(scenarios.keys())}"}

    if scenario_name == "normal":
        for sim in svc.simulators.values():
            sim.fault_mode = None
            sim.fault_steps_remaining = 0
        return {"status": "All stations reset to normal"}

    params = scenarios[scenario_name]
    svc.inject_fault(params["station_id"], params["fault_type"], params["duration"])
    if not svc.is_running:
        svc.start()
    return {"status": "scenario_started", "scenario": scenario_name, **params}
