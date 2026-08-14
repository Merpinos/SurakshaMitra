"""
Tactical Decision Engine for SurakshaMitra.

Evaluates facility infrastructure (gates, neighboring tanks) against
computed threat zone geometries to produce actionable directives
for Incident Commanders.
"""
import json
import os
import math
from typing import Dict, List, Any, Optional

from shapely.geometry import Point, shape


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

_FACILITY_ASSETS: Optional[Dict] = None


def _load_facility_assets() -> Dict:
    """Loads and caches the facility asset registry from disk."""
    global _FACILITY_ASSETS
    if _FACILITY_ASSETS is not None:
        return _FACILITY_ASSETS

    asset_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "facility_assets.json"
    )
    with open(asset_path, "r", encoding="utf-8") as f:
        _FACILITY_ASSETS = json.load(f)
    return _FACILITY_ASSETS


# ---------------------------------------------------------------------------
# Geometry Helpers
# ---------------------------------------------------------------------------

def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns the great-circle distance in meters between two WGS-84 points."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _classify_point_in_zones(
    lat: float,
    lon: float,
    zone_geometries: Dict[str, Any],
) -> Dict[str, bool]:
    """
    Checks whether a (lat, lon) point falls inside each named threat zone.

    Parameters
    ----------
    zone_geometries : dict
        Mapping of zone_name -> Shapely geometry (WGS-84 polygon).

    Returns
    -------
    dict  zone_name -> bool (True if point is inside that zone).
    """
    pt = Point(lon, lat)  # Shapely uses (x=lon, y=lat)
    return {name: geom.contains(pt) for name, geom in zone_geometries.items()}


# ---------------------------------------------------------------------------
# Thermal Flux Estimator (simplified point-source model)
# ---------------------------------------------------------------------------

def _estimate_thermal_flux_kw(
    distance_m: float,
    fireball_radius_m: float,
    mass_kg: float,
) -> float:
    """
    Rough point-source thermal radiation flux at a given distance.

    Q  = η · m · Hc / t_fb        (total emissive power)
    q" = Q / (4π d²)              (flux at distance d)

    Simplified constants:
        η  = 0.25 (radiation fraction)
        Hc = 46 000 kJ/kg  (LPG heat of combustion)
        t_fb = 0.45 · m^0.325  (fireball duration, s)
    """
    if distance_m <= 0 or mass_kg <= 0:
        return 0.0

    eta = 0.25
    Hc = 46_000  # kJ/kg
    t_fb = 0.45 * (mass_kg ** 0.325)  # seconds

    Q = (eta * mass_kg * Hc) / t_fb  # kW
    flux = Q / (4 * math.pi * distance_m ** 2)  # kW/m²
    return round(flux, 2)


# ---------------------------------------------------------------------------
# Gate Feasibility Assessment
# ---------------------------------------------------------------------------

def _evaluate_gates(
    gates: List[Dict],
    origin_lat: float,
    origin_lon: float,
    zone_geometries: Dict[str, Any],
    fireball_radius_m: float,
    mass_kg: float,
) -> List[Dict[str, Any]]:
    """
    For each gate, determine:
      - which threat zones it falls inside
      - estimated thermal flux at gate location
      - tactical status: COMPROMISED | CAUTION | SAFE_ENTRY
    """
    results = []
    for gate in gates:
        g_lat, g_lon = gate["lat"], gate["lon"]
        dist_m = _haversine_distance_m(origin_lat, origin_lon, g_lat, g_lon)
        zone_hits = _classify_point_in_zones(g_lat, g_lon, zone_geometries)
        flux = _estimate_thermal_flux_kw(dist_m, fireball_radius_m, mass_kg)

        # Decision logic
        in_lethal = zone_hits.get("Lethal Threat Zone", False)
        in_severe = zone_hits.get("Severe Threat Zone", False)
        in_moderate = zone_hits.get("Moderate Threat Zone", False)
        in_plume = zone_hits.get("Dispersion Plume", False)
        in_fireball = zone_hits.get("Fireball Radius", False)

        if in_fireball or in_lethal:
            status = "COMPROMISED"
            action = "DO NOT USE — inside lethal/fireball zone"
        elif in_severe:
            status = "COMPROMISED"
            action = f"DO NOT USE — severe overpressure zone ({flux} kW/m²)"
        elif in_moderate or in_plume:
            status = "CAUTION"
            action = f"USE WITH CAUTION — moderate threat / vapor plume ({flux} kW/m²)"
        else:
            status = "SAFE_ENTRY"
            action = f"RECOMMENDED — clear of all threat zones ({flux} kW/m²)"

        results.append({
            "gate_id": gate["id"],
            "gate_name": gate["name"],
            "lat": g_lat,
            "lon": g_lon,
            "distance_from_origin_m": round(dist_m, 1),
            "thermal_flux_kw_m2": flux,
            "zone_exposure": {k: v for k, v in zone_hits.items() if v},
            "status": status,
            "action": action,
        })

    # Sort so SAFE_ENTRY gates appear first (recommended), then CAUTION, then COMPROMISED
    priority = {"SAFE_ENTRY": 0, "CAUTION": 1, "COMPROMISED": 2}
    results.sort(key=lambda g: (priority.get(g["status"], 9), g["distance_from_origin_m"]))
    return results


# ---------------------------------------------------------------------------
# Domino Hazard Assessment
# ---------------------------------------------------------------------------

def _evaluate_domino_tanks(
    tanks: List[Dict],
    origin_lat: float,
    origin_lon: float,
    zone_geometries: Dict[str, Any],
    fireball_radius_m: float,
    mass_kg: float,
) -> List[Dict[str, Any]]:
    """
    For each neighboring (non-origin) tank, determine:
      - which threat zones it falls inside
      - estimated thermal flux
      - domino risk level: BLEVE_RISK | BOILOVER_RISK | MONITOR | CLEAR
      - cooling priority ranking
    """
    results = []
    for tank in tanks:
        if tank.get("is_origin", False):
            continue

        t_lat, t_lon = tank["lat"], tank["lon"]
        dist_m = _haversine_distance_m(origin_lat, origin_lon, t_lat, t_lon)
        zone_hits = _classify_point_in_zones(t_lat, t_lon, zone_geometries)
        flux = _estimate_thermal_flux_kw(dist_m, fireball_radius_m, mass_kg)

        in_fireball = zone_hits.get("Fireball Radius", False)
        in_lethal = zone_hits.get("Lethal Threat Zone", False)
        in_severe = zone_hits.get("Severe Threat Zone", False)
        in_moderate = zone_hits.get("Moderate Threat Zone", False)

        # Domino decision logic
        if in_fireball or in_lethal:
            risk = "BLEVE_RISK"
            action = (
                f"CRITICAL — {tank['name']} is inside the lethal/fireball zone. "
                f"Immediate water-curtain cooling required. Potential BLEVE if unmitigated."
            )
            cooling_priority = 1
        elif in_severe:
            risk = "BOILOVER_RISK"
            action = (
                f"HIGH — {tank['name']} exposed to severe overpressure ({flux} kW/m²). "
                f"Deploy cooling monitors. Risk of boilover for liquid fuels."
            )
            cooling_priority = 2
        elif in_moderate:
            risk = "MONITOR"
            action = (
                f"MODERATE — {tank['name']} in moderate threat zone ({flux} kW/m²). "
                f"Monitor shell temperature. Pre-position cooling resources."
            )
            cooling_priority = 3
        else:
            risk = "CLEAR"
            action = f"{tank['name']} is outside all threat zones ({flux} kW/m²). No immediate action."
            cooling_priority = 99

        results.append({
            "tank_id": tank["id"],
            "tank_name": tank["name"],
            "lat": t_lat,
            "lon": t_lon,
            "fuel_type": tank.get("fuel_type", "Unknown"),
            "capacity": tank.get("capacity", "N/A"),
            "distance_from_origin_m": round(dist_m, 1),
            "thermal_flux_kw_m2": flux,
            "zone_exposure": {k: v for k, v in zone_hits.items() if v},
            "domino_risk": risk,
            "cooling_priority": cooling_priority,
            "action": action,
        })

    results.sort(key=lambda t: (t["cooling_priority"], t["distance_from_origin_m"]))
    return results


# ---------------------------------------------------------------------------
# Plain-English Action Cards
# ---------------------------------------------------------------------------

def _generate_action_cards(
    gate_assessments: List[Dict],
    tank_assessments: List[Dict],
    wind_speed: float,
    wind_dir: float,
) -> List[Dict[str, str]]:
    """
    Generates human-readable tactical directive cards for the
    Incident Commander's heads-up display.
    """
    cards: List[Dict[str, str]] = []

    # Card 1: Recommended approach route
    safe_gates = [g for g in gate_assessments if g["status"] == "SAFE_ENTRY"]
    compromised_gates = [g for g in gate_assessments if g["status"] == "COMPROMISED"]

    if safe_gates:
        best = safe_gates[0]
        avoid_names = ", ".join(g["gate_name"] for g in compromised_gates)
        cards.append({
            "card_type": "APPROACH_ROUTE",
            "severity": "INFO",
            "title": f"Route via {best['gate_name']}",
            "directive": (
                f"Recommended entry point: {best['gate_name']} "
                f"({best['distance_from_origin_m']}m from origin, "
                f"{best['thermal_flux_kw_m2']} kW/m²). "
                + (f"AVOID: {avoid_names}." if avoid_names else "All other gates are also accessible.")
            ),
        })
    else:
        caution_gates = [g for g in gate_assessments if g["status"] == "CAUTION"]
        if caution_gates:
            best = caution_gates[0]
            cards.append({
                "card_type": "APPROACH_ROUTE",
                "severity": "WARNING",
                "title": f"No fully safe gates — use {best['gate_name']} with caution",
                "directive": (
                    f"All gates are inside threat/plume zones. "
                    f"Least hazardous option: {best['gate_name']} "
                    f"({best['thermal_flux_kw_m2']} kW/m²). "
                    f"Full PPE and SCBA mandatory."
                ),
            })
        else:
            cards.append({
                "card_type": "APPROACH_ROUTE",
                "severity": "CRITICAL",
                "title": "ALL GATES COMPROMISED",
                "directive": "All access gates fall within lethal/severe zones. Request aerial or remote approach.",
            })

    # Card 2: Wind advisory
    cardinal_dirs = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ]
    wind_cardinal = cardinal_dirs[int((wind_dir % 360) / 22.5 + 0.5) % 16]
    # Wind blows FROM wind_dir, so downwind is opposite
    downwind_deg = (wind_dir + 180) % 360
    downwind_cardinal = cardinal_dirs[int(downwind_deg / 22.5 + 0.5) % 16]

    cards.append({
        "card_type": "WIND_ADVISORY",
        "severity": "WARNING",
        "title": f"Wind from {wind_cardinal} at {wind_speed} m/s",
        "directive": (
            f"Vapor plume is dispersing towards {downwind_cardinal}. "
            f"Approach from upwind ({wind_cardinal} side) whenever possible. "
            f"Deploy vapor detection on {downwind_cardinal} perimeter."
        ),
    })

    # Card 3: Domino cooling priorities
    critical_tanks = [t for t in tank_assessments if t["domino_risk"] in ("BLEVE_RISK", "BOILOVER_RISK")]
    if critical_tanks:
        target_list = "; ".join(
            f"{t['tank_name']} [{t['domino_risk']}] @ {t['distance_from_origin_m']}m"
            for t in critical_tanks
        )
        cards.append({
            "card_type": "COOLING_PRIORITY",
            "severity": "CRITICAL",
            "title": f"{len(critical_tanks)} tank(s) require immediate cooling",
            "directive": (
                f"Priority cooling targets: {target_list}. "
                f"Deploy water monitors and deluge systems immediately. "
                f"Monitor shell temperatures every 60 seconds."
            ),
        })
    else:
        cards.append({
            "card_type": "COOLING_PRIORITY",
            "severity": "INFO",
            "title": "No immediate domino cooling required",
            "directive": "All neighboring tanks are outside critical threat zones. Continue monitoring.",
        })

    return cards


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_tactical_situation(
    facility_id: Optional[str],
    origin_lat: float,
    origin_lon: float,
    mass_kg: float,
    fireball_radius_m: float,
    wind_speed: float,
    wind_dir: float,
    zone_features: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Main entry point for the Tactical Decision Engine.

    Parameters
    ----------
    facility_id : str | None
        The selected facility ID.
    origin_lat, origin_lon : float
        Coordinates of the incident origin.
    mass_kg : float
        Fuel mass involved in the incident.
    fireball_radius_m : float
        Pre-computed BLEVE fireball radius (meters).
    wind_speed : float
        Wind speed in m/s.
    wind_dir : float
        Wind direction in degrees (meteorological, 0-360).
    zone_features : list[dict]
        The GeoJSON features list from `/compute-zone`, each containing
        a `properties.zone_name` and a `geometry` dict.

    Returns
    -------
    dict
        Tactical summary with gate assessments, domino assessments,
        and plain-English action cards.
    """
    # Rebuild Shapely geometries from GeoJSON features
    zone_geometries: Dict[str, Any] = {}
    for feat in zone_features:
        name = feat["properties"]["zone_name"]
        zone_geometries[name] = shape(feat["geometry"])

    # Load facility assets
    all_assets = _load_facility_assets()
    
    if not facility_id or facility_id == "custom" or facility_id not in all_assets:
        return {
            "gate_access": [],
            "domino_hazards": [],
            "action_cards": [{
                "card_type": "INFO",
                "severity": "INFO",
                "title": "Custom Location",
                "directive": "Tactical copilot requires a known facility preset. Showing generic zones only."
            }],
        }
        
    assets = all_assets[facility_id]

    # Evaluate gates
    gate_assessments = _evaluate_gates(
        gates=assets["gates"],
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        zone_geometries=zone_geometries,
        fireball_radius_m=fireball_radius_m,
        mass_kg=mass_kg,
    )

    # Evaluate domino tanks
    tank_assessments = _evaluate_domino_tanks(
        tanks=assets["tanks"],
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        zone_geometries=zone_geometries,
        fireball_radius_m=fireball_radius_m,
        mass_kg=mass_kg,
    )

    # Generate action cards
    action_cards = _generate_action_cards(
        gate_assessments=gate_assessments,
        tank_assessments=tank_assessments,
        wind_speed=wind_speed,
        wind_dir=wind_dir,
    )

    return {
        "gate_access": gate_assessments,
        "domino_hazards": tank_assessments,
        "action_cards": action_cards,
    }
