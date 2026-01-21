"""
Building data structure and main interface.

A building is defined by:
- One footprint per floor (can be different shapes, can overhang)
- Building-level parameters (floor height, style, etc.)
- Hierarchical lazy generation of exterior elements
"""

from typing import List, Optional, Dict, Any
from .footprint import Footprint, Point2D


class Building:
    """
    Main building structure.
    
    Represents a multi-floor building with lazy generation of all sub-elements.
    """
    
    def __init__(
        self,
        floor_footprints: List[List[Point2D]],
        seed: int,
        floor_height: float = 3.0,
        **params
    ):
        """
        Initialize building.
        
        Args:
            floor_footprints: List of vertex lists, one per floor (bottom to top)
            seed: Seed for deterministic generation
            floor_height: Height of each floor in meters
            **params: Additional building parameters (style, material, etc.)
        """
        self.floor_footprints = [Footprint(vertices) for vertices in floor_footprints]
        self.seed = seed
        self.floor_height = floor_height
        self.params = params
        
        # Lazy caches
        self._walls: Optional[List] = None
        self._exterior: Optional[Any] = None
    
    @property
    def num_floors(self) -> int:
        """Number of floors in building."""
        return len(self.floor_footprints)
    
    def get_floor_footprint(self, floor_idx: int) -> Footprint:
        """Get footprint for specific floor (0-indexed from bottom)."""
        return self.floor_footprints[floor_idx]
    
    def get_walls(self, **params) -> List:
        """
        Get all walls in building (lazy generation).
        
        This triggers wall generation from floor footprints.
        
        Args:
            **params: Wall generation parameters
            
        Returns:
            List of Wall objects
        """
        if self._walls is None:
            # TODO: Call wall generator
            pass
        return self._walls
    
    def get_exterior(self, **params) -> Any:
        """
        Get complete exterior structure (lazy generation).
        
        This generates walls, corners, windows, doors as a complete structure.
        
        Args:
            **params: Exterior generation parameters
            
        Returns:
            Exterior structure object
        """
        if self._exterior is None:
            # TODO: Call exterior generator
            pass
        return self._exterior
