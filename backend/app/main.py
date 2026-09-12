"""
SkyGuard AI - FastAPI Application Entry Point
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings, DB_DIR
from .database.connection import init_db
from .api.routes import router
from .api.simulation_routes import sim_router
from .api.noaa_routes import noaa_router
from .services.simulation_service import SimulationService, set_sim_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SkyGuard AI backend initializing...")
    os.makedirs(DB_DIR, exist_ok=True)
    await init_db()
    logger.info("Database schemas created")

    sim_service = SimulationService()
    set_sim_service(sim_service)
    await sim_service.initialize()
    logger.info("Simulation service initialized")

    yield

    if sim_service:
        sim_service.stop()
    logger.info("SkyGuard AI shutdown complete")

app = FastAPI(
    title="SkyGuard AI",
    description="AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(sim_router, prefix="/api")
app.include_router(noaa_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "name": "SkyGuard AI",
        "version": "1.0.0",
        "status": "operational",
        "mission": "Can we trust the weather data before we trust the forecast?"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
