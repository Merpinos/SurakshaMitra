"""
Local test script for /compute-zone with Tactical Decision Engine.
Uses FastAPI's TestClient to invoke the endpoint and prints the full JSON.
"""
import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

payload = {
    "lat": 26.8505,
    "lon": 75.8069,
    "fuel_type": "LPG",
    "mass_kg": 2700000.0,
    "storage_type": "bullet",
    "wind_speed": 5.0,
    "wind_dir": 315.0,
}

resp = client.post("/compute-zone", json=payload)
data = resp.json()

# Print only metadata + tactical_summary (skip polygon coordinates for readability)
output = {
    "metadata": data.get("metadata"),
    "feature_count": len(data.get("features", [])),
    "feature_zone_names": [f["properties"]["zone_name"] for f in data.get("features", [])],
    "tactical_summary": data.get("tactical_summary"),
}

print(json.dumps(output, indent=2))
