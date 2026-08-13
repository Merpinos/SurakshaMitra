"""
Generate Fallback GeoJSON script for SurakshaMitra.
Imports blast and thermal models and generates jaipur_demo.json.
"""
import os
import json
from backend.main import ZoneRequest, compute_zone


def generate_jaipur_fallback():
    # Jaipur IOCL validation case input parameters
    request = ZoneRequest(
        lat=26.8505,
        lon=75.8069,
        fuel_type="LPG",
        mass_kg=2700000.0,
        storage_type="bullet",
        wind_speed=5.0,
        wind_dir=315.0
    )

    # Compute GeoJSON payload
    geojson_data = compute_zone(request)

    # Path to frontend/data/jaipur_demo.json
    output_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "jaipur_demo.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)

    print(f"Successfully generated fallback GeoJSON at: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    generate_jaipur_fallback()
