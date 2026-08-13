"""
SurakshaMitra - Hazardous Industrial Facility Threat Zone Visualizer API
FastAPI Backend
"""
import math
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from shapely.geometry import Point, mapping
from shapely.ops import transform
import shapely.affinity
from pyproj import CRS, Transformer

from backend.models.blast import compute_blast_radii
from backend.models.thermal import compute_fireball_radius

app = FastAPI(
    title="SurakshaMitra API",
    description="Hazardous Industrial Facility Threat Zone Visualizer API",
    version="1.0.0"
)

# CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ZoneRequest(BaseModel):
    lat: float = Field(..., description="Latitude of facility", example=26.8505)
    lon: float = Field(..., description="Longitude of facility", example=75.8069)
    fuel_type: str = Field(..., description="Fuel type (LPG, Petrol, Crude)", example="LPG")
    mass_kg: float = Field(..., description="Fuel mass in kg", example=2700000.0)
    storage_type: str = Field(default="bullet", description="Storage type (bullet, sphere, tank)")
    wind_speed: float = Field(default=5.0, description="Wind speed in m/s")
    wind_dir: float = Field(default=315.0, description="Wind direction in degrees (0-360)")

    @field_validator("mass_kg")
    def validate_mass(cls, v):
        if v <= 0:
            raise ValueError("mass_kg must be greater than 0")
        return v


def buffer_in_meters(lat: float, lon: float, radius_m: float) -> Any:
    """
    Creates a geodesic circular polygon of specified radius in meters centered at (lat, lon).
    Uses Azimuthal Equidistant projection for metric accuracy.
    """
    proj_aeqd = CRS(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
    proj_wgs84 = CRS("EPSG:4326")

    transformer_to_wgs84 = Transformer.from_crs(proj_aeqd, proj_wgs84, always_xy=True)

    # Point at (0,0) in AEQD projection is the target (lon, lat)
    center_point = Point(0, 0)
    circle_aeqd = center_point.buffer(radius_m, quad_segs=32)

    # Transform geometry back to lat/lon WGS84
    circle_wgs84 = transform(transformer_to_wgs84.transform, circle_aeqd)
    return circle_wgs84


def create_dispersion_plume(lat: float, lon: float, moderate_r_m: float, wind_speed: float, wind_dir: float) -> Any:
    """
    Creates an elongated, rotated dispersion plume ellipse in downwind direction.
    """
    proj_aeqd = CRS(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
    proj_wgs84 = CRS("EPSG:4326")

    transformer_to_wgs84 = Transformer.from_crs(proj_aeqd, proj_wgs84, always_xy=True)

    # Base shape in metric space
    base_circle = Point(0, 0).buffer(moderate_r_m, quad_segs=32)

    # Elongate downwind based on wind speed
    x_scale = 1.25 + (wind_speed * 0.08)
    y_scale = 0.70
    scaled_ellipse = shapely.affinity.scale(base_circle, xfact=x_scale, yfact=y_scale, origin=(0, 0))

    # Shift plume downwind so origin is upwind inside the plume
    x_offset = moderate_r_m * (0.15 + wind_speed * 0.05)
    translated_ellipse = shapely.affinity.translate(scaled_ellipse, xoff=x_offset, yoff=0)

    # Rotate by math angle: 270 - wind_dir (counter-clockwise from East)
    math_angle = (270.0 - wind_dir) % 360.0
    rotated_plume = shapely.affinity.rotate(translated_ellipse, math_angle, origin=(0, 0), use_radians=False)

    # Transform back to WGS84 coordinates
    plume_wgs84 = transform(transformer_to_wgs84.transform, rotated_plume)
    return plume_wgs84


@app.get("/")
def read_root():
    return {
        "app": "SurakshaMitra API",
        "status": "online",
        "documentation": "/docs"
    }


@app.post("/compute-zone")
def compute_zone(req: ZoneRequest) -> Dict[str, Any]:
    """
    Computes explosion threat zones, BLEVE fireball radius, and dispersion plume.
    Returns GeoJSON FeatureCollection containing polygons with styling properties.
    """
    try:
        blast_info = compute_blast_radii(req.mass_kg, req.fuel_type)
        r_fireball = compute_fireball_radius(req.mass_kg)

        r_lethal = blast_info["lethal_m"]
        r_severe = blast_info["severe_m"]
        r_moderate = blast_info["moderate_m"]

        # Generate geometries
        geom_fireball = buffer_in_meters(req.lat, req.lon, r_fireball)
        geom_lethal = buffer_in_meters(req.lat, req.lon, r_lethal)
        geom_severe = buffer_in_meters(req.lat, req.lon, r_severe)
        geom_moderate = buffer_in_meters(req.lat, req.lon, r_moderate)
        geom_plume = create_dispersion_plume(req.lat, req.lon, r_moderate, req.wind_speed, req.wind_dir)

        features = [
            {
                "type": "Feature",
                "properties": {
                    "zone_name": "Dispersion Plume",
                    "radius_m": round(r_moderate * (1.25 + req.wind_speed * 0.08), 1),
                    "overpressure_kpa": "Gas/Vapor Plume",
                    "color": "#2563eb",
                    "fill_color": "#3b82f6",
                    "fill_opacity": 0.30,
                    "wind_speed_ms": req.wind_speed,
                    "wind_dir_deg": req.wind_dir,
                },
                "geometry": mapping(geom_plume)
            },
            {
                "type": "Feature",
                "properties": {
                    "zone_name": "Moderate Threat Zone",
                    "radius_m": r_moderate,
                    "overpressure_kpa": "> 7 kPa",
                    "color": "#ca8a04",
                    "fill_color": "#eab308",
                    "fill_opacity": 0.35,
                },
                "geometry": mapping(geom_moderate)
            },
            {
                "type": "Feature",
                "properties": {
                    "zone_name": "Severe Threat Zone",
                    "radius_m": r_severe,
                    "overpressure_kpa": "> 34 kPa",
                    "color": "#ea580c",
                    "fill_color": "#f97316",
                    "fill_opacity": 0.35,
                },
                "geometry": mapping(geom_severe)
            },
            {
                "type": "Feature",
                "properties": {
                    "zone_name": "Lethal Threat Zone",
                    "radius_m": r_lethal,
                    "overpressure_kpa": "> 83 kPa",
                    "color": "#dc2626",
                    "fill_color": "#ef4444",
                    "fill_opacity": 0.35,
                },
                "geometry": mapping(geom_lethal)
            },
            {
                "type": "Feature",
                "properties": {
                    "zone_name": "Fireball Radius",
                    "radius_m": r_fireball,
                    "overpressure_kpa": "Thermal BLEVE",
                    "color": "#991b1b",
                    "fill_color": "#dc2626",
                    "fill_opacity": 0.50,
                },
                "geometry": mapping(geom_fireball)
            }
        ]

        return {
            "type": "FeatureCollection",
            "metadata": {
                "facility": {
                    "lat": req.lat,
                    "lon": req.lon,
                    "fuel_type": req.fuel_type,
                    "mass_kg": req.mass_kg,
                    "storage_type": req.storage_type,
                    "tnt_equivalent_kg": blast_info["tnt_equivalent_kg"],
                    "fireball_radius_m": r_fireball,
                    "wind_speed": req.wind_speed,
                    "wind_dir": req.wind_dir,
                }
            },
            "features": features
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
