import json
import urllib.request
from typing import Tuple

def get_live_wind(lat: float, lon: float) -> Tuple[float, float]:
    """
    Fetches real-time wind data from Open-Meteo API.
    Returns (wind_speed_ms, wind_direction_deg).
    If the API call fails, defaults to (5.0, 0.0).
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=wind_speed_10m,wind_direction_10m"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SurakshaMitra/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                current = data.get('current', {})
                wind_speed_kmh = current.get('wind_speed_10m', 18.0)
                wind_dir = current.get('wind_direction_10m', 0.0)
                
                # Convert km/h to m/s
                wind_speed_ms = round(wind_speed_kmh / 3.6, 1)
                return float(wind_speed_ms), float(wind_dir)
    except Exception as e:
        print(f"Failed to fetch live weather: {e}")
        
    return 5.0, 0.0
