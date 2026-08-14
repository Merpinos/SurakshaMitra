import json

path = "d:/SIH/backend/data/facility_assets.json"
with open(path, "r", encoding="utf-8") as f:
    jaipur_data = json.load(f)

new_data = {
    "jaipur_iocl": jaipur_data,
    "vizag_hpcl": {
        "facility_id": "HPCL_VIZAG_TERMINAL",
        "plant_center": {"lat": 17.6868, "lon": 83.2185},
        "gates": [
            {"id": "G1", "name": "Vizag North Gate", "lat": 17.6880, "lon": 83.2185, "type": "main_entry", "description": ""},
            {"id": "G2", "name": "Vizag South Gate", "lat": 17.6850, "lon": 83.2185, "type": "secondary_entry", "description": ""}
        ],
        "tanks": [
            {"id": "T-201", "name": "Crude Tank 1", "lat": 17.6868, "lon": 83.2185, "fuel_type": "Crude", "capacity": "5000KL", "storage_type": "tank", "is_origin": True},
            {"id": "T-202", "name": "Crude Tank 2", "lat": 17.6875, "lon": 83.2190, "fuel_type": "Crude", "capacity": "3000KL", "storage_type": "tank", "is_origin": False}
        ]
    },
    "mangalore_mrpl": {
        "facility_id": "MRPL_MANGALORE",
        "plant_center": {"lat": 12.8916, "lon": 74.8430},
        "gates": [
            {"id": "G1", "name": "MRPL Main Gate", "lat": 12.8930, "lon": 74.8430, "type": "main_entry", "description": ""},
            {"id": "G2", "name": "MRPL East Gate", "lat": 12.8916, "lon": 74.8450, "type": "secondary_entry", "description": ""}
        ],
        "tanks": [
            {"id": "T-301", "name": "Petrol Tank 1", "lat": 12.8916, "lon": 74.8430, "fuel_type": "Petrol", "capacity": "3500KL", "storage_type": "tank", "is_origin": True},
            {"id": "T-302", "name": "Petrol Tank 2", "lat": 12.8920, "lon": 74.8440, "fuel_type": "Petrol", "capacity": "2000KL", "storage_type": "tank", "is_origin": False}
        ]
    },
    "bina_bpcl": {
        "facility_id": "BPCL_BINA",
        "plant_center": {"lat": 24.1700, "lon": 78.1800},
        "gates": [
            {"id": "G1", "name": "Bina North Gate", "lat": 24.1720, "lon": 78.1800, "type": "main_entry", "description": ""},
            {"id": "G2", "name": "Bina West Gate", "lat": 24.1700, "lon": 78.1780, "type": "secondary_entry", "description": ""}
        ],
        "tanks": [
            {"id": "T-401", "name": "LPG Sphere 1", "lat": 24.1700, "lon": 78.1800, "fuel_type": "LPG", "capacity": "1800T", "storage_type": "sphere", "is_origin": True},
            {"id": "T-402", "name": "LPG Sphere 2", "lat": 24.1710, "lon": 78.1810, "fuel_type": "LPG", "capacity": "1000T", "storage_type": "sphere", "is_origin": False}
        ]
    }
}

with open(path, "w", encoding="utf-8") as f:
    json.dump(new_data, f, indent=2)
