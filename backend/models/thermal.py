"""
Thermal Radiation Module for Fireball Radius Calculation.
"""

def compute_fireball_radius(mass_kg: float) -> float:
    """
    Computes BLEVE fireball radius in meters.
    Formula: r = 3.86 * (mass_kg ^ 0.325)
    """
    if mass_kg <= 0:
        return 0.0
    r_fireball = 3.86 * (mass_kg ** 0.325)
    return round(r_fireball, 2)
