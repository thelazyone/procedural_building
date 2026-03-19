"""
Building parameter generator.

Derives randomized building parameters (height, window density, etc.)
from a unique seed. Each building gets deterministic but varied parameters.
"""

import random
from typing import Dict, Any


# Default ranges for each parameter (min, max)
PARAM_RANGES = {
    "floor_height": (2.5, 3.5),
    "door_density": (0.03, 0.08),
    # Upper floors: each above-occlusion segment rolls this (0–1) to allow a door
    "above_occlusion_door_chance": (0.5, 0.88),
    "window_density": (0.2, 0.45),
    "window_fill_prob": (0.55, 0.85),   # Probability of placing window at valid slot (avg ~0.275) - many empty slots
    "front_window_density_mult": (1.5, 2.1),  # Avg 1.8 - tighter spacing = more windows
    "back_window_density_mult": (1.0, 1.4),   # Avg 1.2 - looser spacing = fewer windows
    "corner_size": (0.1, 0.25),
    "edge_spacing": (0.8, 1.2),
    "roof_protrusion": (0.0, 0.2),   # How much roof extends on front facades only (meters)
    "roof_height": (0.3, 1.2),       # Roof prism height on top of building (meters)
}


def generate_building_params(seed: int) -> Dict[str, Any]:
    """
    Generate building parameters from a unique seed.

    Each building with a given seed will always get the same parameters.
    Different seeds produce varied but deterministic parameters.

    Args:
        seed: Unique seed for this building (e.g. from derive_seed)

    Returns:
        Dictionary of parameters suitable for Building/FloorGenerator:
        - floor_height: Height per floor in meters
        - door_density: Ground floor — doors per meter of perimeter
        - above_occlusion_door_chance: Upper floors — probability per eligible segment
        - window_density: Windows per meter of perimeter
        - window_fill_prob: Probability of placing window at valid slot (0-1)
        - front_window_density_mult: Front facade slot spacing multiplier (avg 1.8)
        - back_window_density_mult: Back facade slot spacing multiplier (avg 1.2)
        - corner_size: Corner element size in meters
        - edge_spacing: Min spacing from edges for placement
        - roof_protrusion: Roof overhang on front facades only (meters)
        - roof_height: Roof prism height on top of building (meters)
    """
    rng = random.Random(seed)
    params = {}
    for key, (lo, hi) in PARAM_RANGES.items():
        params[key] = rng.uniform(lo, hi)
    return params
