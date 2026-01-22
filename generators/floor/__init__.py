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
        **params
    ) -> Dict[str, Any]:
        """
        Generate all floor elements.
        
        Args:
            parent_context: Floor object
            seed: Generation seed
            door_density: Number of doors per meter of perimeter
            window_density: Number of windows per meter of perimeter
            edge_spacing: Minimum spacing from edge corners for element placement
            **params: Additional parameters passed to sub-generators
            
        Returns:
            Dictionary with 'doors', 'windows', and 'corners' lists
        """
        floor = parent_context
        
        # Generate doors (only on ground floor)
        # Returns both doors and occupied segments for collision avoidance
        doors, door_occupied_segments = generate_doors(
            floor=floor,
            seed=self.derive_seed(seed, "doors"),
            door_density=door_density,
            edge_spacing=edge_spacing,
            **params
        )
        
        # Generate windows (on all floors)
        # Pass door occupied segments to avoid collisions
        windows = generate_windows(
            floor=floor,
            seed=self.derive_seed(seed, "windows"),
            door_occupied_segments=door_occupied_segments,
            window_density=window_density,
            edge_spacing=edge_spacing,
            **params
        )
        
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
