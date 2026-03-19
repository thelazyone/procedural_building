"""
Floor generator module.

Orchestrates the generation of floor elements (doors, windows, corners)
by calling separate placement logic modules.
"""

from typing import Dict, Any
from core.generator_base import GeneratorBase
from .floor import Floor
from .floor_doors import generate_doors
from .floor_windows import generate_windows
from .floor_corners import generate_corners


class FloorGenerator(GeneratorBase):
    """
    Generates floor elements (doors, windows, corners) based on floor footprint.
    
    This generator orchestrates the placement logic by calling separate modules:
    - floor_doors: handles door placement logic
    - floor_windows: handles window placement logic
    - floor_corners: handles corner placement logic
    """
    
    def generate(
        self,
        parent_context: Floor,
        seed: int,
        door_density: float = 0.05,
        window_density: float = 0.3,
        edge_spacing: float = 1.0,
        above_occlusion_door_chance: float = 0.3,
        window_spacing: float = 1.5,
        door_spacing: float = 2.0,
        **params
    ) -> Dict[str, Any]:
        """
        Generate all floor elements.
        Order: windows first, then doors (doors ignore windows), then remove
        windows that conflict with door margins.
        """
        floor = parent_context
        
        # 1. Generate windows first (no door avoidance yet)
        windows = generate_windows(
            floor=floor,
            seed=self.derive_seed(seed, "windows"),
            door_occupied_segments=[],  # Empty - doors not placed yet
            window_density=window_density,
            edge_spacing=edge_spacing,
            window_spacing=window_spacing,
            **params
        )
        
        # 2. Generate doors (ignore window positions)
        doors, door_occupied_segments = generate_doors(
            floor=floor,
            seed=self.derive_seed(seed, "doors"),
            door_density=door_density,
            edge_spacing=edge_spacing,
            door_spacing=door_spacing,
            above_occlusion_door_chance=above_occlusion_door_chance,
            **params
        )
        
        # 3. Remove windows that conflict with door margins
        if door_occupied_segments:
            door_margin = door_spacing  # Windows within door_spacing of door center are removed
            filtered_windows = []
            for w in windows:
                if w.edge_idx >= len(door_occupied_segments):
                    filtered_windows.append(w)
                    continue
                edge_len = (
                    (w.edge_end[0] - w.edge_start[0]) ** 2 +
                    (w.edge_end[1] - w.edge_start[1]) ** 2
                ) ** 0.5
                abs_pos = w.position_on_edge * edge_len
                conflict = any(
                    not (abs_pos + window_spacing / 2 < os or abs_pos - window_spacing / 2 > oe)
                    for os, oe in door_occupied_segments[w.edge_idx]
                )
                if not conflict:
                    filtered_windows.append(w)
            windows = filtered_windows
        
        # Generate corners (at all vertices)
        corners = generate_corners(
            floor=floor,
            seed=self.derive_seed(seed, "corners"),
            **params
        )
        
        return {
            'doors': doors,
            'windows': windows,
            'corners': corners
        }


# Export FloorGenerator for easy import
__all__ = ['FloorGenerator']
