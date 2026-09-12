"""
SkyGuard AI - Dynamic Spatial Consistency Analyzer
Cross-verifies target AWS station observations against geographically proximate peer stations
using ONLY the three approved meteorological parameters: Temperature, Pressure, Relative Humidity.
Includes Haversine geographic distance filtering and dynamic N-station scalability.
"""
import math
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@dataclass
class SpatialConsistencyResult:
    spatial_anomaly_detected: bool
    regional_pattern: str # SUPPORTED | NOT_SUPPORTED | INSUFFICIENT_EVIDENCE
    temperature_delta: float
    pressure_delta: float
    humidity_delta: float
    neighbor_count: int
    confidence_boost: float
    description: str

class SpatialAnalyzer:
    """
    Evaluates spatial agreement between a target station reading and nearby AWS stations.
    Supports dynamic N-station scaling based on geographic coordinates.
    """
    def filter_neighbors_by_distance(
        self,
        target_lat: Optional[float],
        target_lon: Optional[float],
        all_stations_readings: List[Dict[str, Any]],
        max_radius_km: float = 1200.0,
        max_neighbors: int = 5
    ) -> List[Dict[str, Any]]:
        """Finds nearest neighbor station readings within geographic radius."""
        if target_lat is None or target_lon is None or not all_stations_readings:
            return all_stations_readings[:max_neighbors] if all_stations_readings else []

        scored = []
        for r in all_stations_readings:
            lat = r.get("latitude")
            lon = r.get("longitude")
            if lat is not None and lon is not None:
                dist = haversine_distance_km(target_lat, target_lon, lat, lon)
                if dist > 0.1 and dist <= max_radius_km: # Exclude self
                    scored.append((dist, r))
            else:
                scored.append((9999.0, r))

        scored.sort(key=lambda x: x[0])
        return [item[1] for item in scored[:max_neighbors]]

    def analyze(
        self,
        target_record: Dict[str, Any],
        neighbor_records: List[Dict[str, Any]],
        temp_threshold: float = 6.5,
        pressure_threshold: float = 10.0,
        humidity_threshold: float = 20.0
    ) -> SpatialConsistencyResult:
        """
        Evaluates spatial agreement across Temperature, Pressure, and Humidity.
        Returns explicit regional pattern state: SUPPORTED, NOT_SUPPORTED, or INSUFFICIENT_EVIDENCE.
        """
        if not neighbor_records:
            return SpatialConsistencyResult(
                spatial_anomaly_detected=False,
                regional_pattern="INSUFFICIENT_EVIDENCE",
                temperature_delta=0.0,
                pressure_delta=0.0,
                humidity_delta=0.0,
                neighbor_count=0,
                confidence_boost=0.0,
                description="Spatial Evidence: Insufficient nearby AWS observations available for regional verification."
            )

        # Filter out records missing all 3 parameters
        valid_neighbors = [
            r for r in neighbor_records
            if not r.get("is_missing", False) and
            any(r.get(p) is not None for p in ["temperature", "pressure", "humidity"])
        ]

        if not valid_neighbors:
            return SpatialConsistencyResult(
                spatial_anomaly_detected=False,
                regional_pattern="INSUFFICIENT_EVIDENCE",
                temperature_delta=0.0,
                pressure_delta=0.0,
                humidity_delta=0.0,
                neighbor_count=0,
                confidence_boost=0.0,
                description="Spatial Evidence: Insufficient valid neighboring telemetry (all nearby sensors missing or offline)."
            )

        valid_temps = [r['temperature'] for r in valid_neighbors if r.get('temperature') is not None]
        valid_press = [r['pressure'] for r in valid_neighbors if r.get('pressure') is not None]
        valid_hums = [r['humidity'] for r in valid_neighbors if r.get('humidity') is not None]

        target_temp = target_record.get('temperature')
        target_press = target_record.get('pressure')
        target_hum = target_record.get('humidity')

        temp_delta = 0.0
        if target_temp is not None and valid_temps:
            mean_temp = float(np.mean(valid_temps))
            temp_delta = abs(target_temp - mean_temp)

        press_delta = 0.0
        if target_press is not None and valid_press:
            mean_press = float(np.mean(valid_press))
            press_delta = abs(target_press - mean_press)

        hum_delta = 0.0
        if target_hum is not None and valid_hums:
            mean_hum = float(np.mean(valid_hums))
            hum_delta = abs(target_hum - mean_hum)

        is_spatial_anomaly = (
            temp_delta > temp_threshold or
            press_delta > pressure_threshold or
            hum_delta > humidity_threshold
        )

        # Check for coherent regional weather event (peers also changing)
        coherent_regional_shift = False
        if valid_temps and len(valid_temps) >= 2:
            temp_std = float(np.std(valid_temps))
            press_std = float(np.std(valid_press)) if valid_press else 0.0
            # If peer stations have high variance together, it indicates a regional weather front
            if temp_std > 3.0 or press_std > 5.0:
                coherent_regional_shift = True

        if is_spatial_anomaly and not coherent_regional_shift:
            regional_pattern = "NOT_SUPPORTED"
            conf_boost = 0.15
            desc_parts = []
            if temp_delta > temp_threshold:
                desc_parts.append(f"Temperature deviates by {round(temp_delta, 1)}°C from nearby AWS average ({round(np.mean(valid_temps), 1)}°C).")
            if press_delta > pressure_threshold:
                desc_parts.append(f"Pressure deviates by {round(press_delta, 1)} hPa from nearby AWS average ({round(np.mean(valid_press), 1)} hPa).")
            if hum_delta > humidity_threshold:
                desc_parts.append(f"Humidity deviates by {round(hum_delta, 1)}% from nearby AWS average ({round(np.mean(valid_hums), 1)}%).")
            desc = f"Spatial Evidence (NOT SUPPORTED): Nearby AWS stations ({len(valid_neighbors)}) remained normal while target station reported sharp deviation. " + " ".join(desc_parts)
        elif coherent_regional_shift or not is_spatial_anomaly:
            regional_pattern = "SUPPORTED"
            conf_boost = 0.0
            desc = f"Spatial Evidence (SUPPORTED): Regional atmospheric agreement verified across {len(valid_neighbors)} nearby AWS stations."
            is_spatial_anomaly = False
        else:
            regional_pattern = "INSUFFICIENT_EVIDENCE"
            conf_boost = 0.0
            desc = f"Spatial Evidence: Insufficient regional trend correlation across {len(valid_neighbors)} nearby AWS stations."

        return SpatialConsistencyResult(
            spatial_anomaly_detected=is_spatial_anomaly,
            regional_pattern=regional_pattern,
            temperature_delta=round(temp_delta, 2),
            pressure_delta=round(press_delta, 2),
            humidity_delta=round(hum_delta, 2),
            neighbor_count=len(valid_neighbors),
            confidence_boost=conf_boost,
            description=desc
        )
