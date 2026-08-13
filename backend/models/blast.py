"""
Blast Threat Zone Calculation Module using TNT Equivalence and Hopkinson Scaling.
"""
from typing import Dict, Tuple

TNT_EQUIVALENCE_FACTORS: Dict[str, float] = {
    "LPG": 0.70,
    "Petrol": 0.84,
    "Crude": 0.65,
}

DEFAULT_TNT_FACTOR = 0.70


def compute_tnt_equivalent_mass(mass_kg: float, fuel_type: str) -> float:
    """
    Computes equivalent TNT mass in kg based on fuel type.
    """
    factor = TNT_EQUIVALENCE_FACTORS.get(fuel_type.strip(), DEFAULT_TNT_FACTOR)
    return mass_kg * factor


def compute_blast_radii(mass_kg: float, fuel_type: str) -> Dict[str, float]:
    """
    Computes blast radii in meters for Lethal (>83 kPa), Severe (>34 kPa),
    and Moderate (>7 kPa) overpressure threat zones.
    
    Formula: R = k * (TNT_mass_kg)^(1/3)
    k_lethal = 2.2
    k_severe = 3.5
    k_moderate = 6.8
    """
    tnt_mass = compute_tnt_equivalent_mass(mass_kg, fuel_type)
    tnt_cube_root = tnt_mass ** (1.0 / 3.0)

    r_lethal = 2.2 * tnt_cube_root
    r_severe = 3.5 * tnt_cube_root
    r_moderate = 6.8 * tnt_cube_root

    return {
        "tnt_equivalent_kg": round(tnt_mass, 2),
        "lethal_m": round(r_lethal, 2),
        "severe_m": round(r_severe, 2),
        "moderate_m": round(r_moderate, 2),
    }
