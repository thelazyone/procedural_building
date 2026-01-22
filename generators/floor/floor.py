"""
Floor data structure.

A floor represents a single level of a building, containing:
- Footprint (2D outline)
- Height (vertical dimension)
- Eventually: rooms, walls, doors, corners
"""

from typing import List, Optional, Any
from core.footprint import Footprint, Point2D


class Floor:
    """
    Represents a single floor in a building.
    
    Contains the footprint outline and floor-specific parameters.
    Future: will contain rooms, walls, doors, corners.
    """
    
    def __init__(
        self,
        footprint: Footprint,
        height: float = 3.0,
        floor_idx: int = 0,
        **params
    ):
        """
        Initialize floor.
        
        Args:
            footprint: The 2D outline of this floor
            height: Height of this floor in meters
            floor_idx: Index of this floor (0 = ground floor)
            **params: Additional floor parameters (style, material, etc.)
        """
        self.footprint = footprint
        self.height = height
        self.floor_idx = floor_idx
        self.params = params
        
        # Lazy caches for generated elements
        self._rooms: Optional[List] = None
        self._walls: Optional[List] = None
        self._doors: Optional[List] = None
        self._windows: Optional[List] = None
        self._corners: Optional[List] = None
        self._generated: bool = False
    
    @classmethod
    def from_vertices(
        cls,
        vertices: List[Point2D],
        height: float = 3.0,
        floor_idx: int = 0,
        **params
    ) -> 'Floor':
        """
        Create floor from vertex list.
        
        Args:
            vertices: List of (x, y) tuples defining floor outline
            height: Height of this floor in meters
            floor_idx: Index of this floor
            **params: Additional parameters
            
        Returns:
            Floor object
        """
        footprint = Footprint(vertices)
        return cls(footprint, height, floor_idx, **params)
    
    def get_z_base(self, cumulative_heights: List[float]) -> float:
        """
        Get the base Z coordinate of this floor.
        
        Args:
            cumulative_heights: Cumulative heights from building
            
        Returns:
            Z coordinate of floor base
        """
        return cumulative_heights[self.floor_idx] if self.floor_idx < len(cumulative_heights) else 0.0
    
    def get_z_top(self, cumulative_heights: List[float]) -> float:
        """
        Get the top Z coordinate of this floor.
        
        Args:
            cumulative_heights: Cumulative heights from building
            
        Returns:
            Z coordinate of floor top
        """
        base = self.get_z_base(cumulative_heights)
        return base + self.height
    
    def generate_elements(self, seed: int, **generation_params):
        """
        Generate floor elements (doors, windows, etc.) lazily.
        
        Args:
            seed: Generation seed
            **generation_params: Parameters for generation (door_density, window_density, etc.)
        """
        if self._generated:
            return
        
        # Import here to avoid circular dependency
        from generators.floor import FloorGenerator
        
        generator = FloorGenerator()
        result = generator.generate(self, seed, **generation_params)
        
        self._doors = result.get('doors', [])
        self._windows = result.get('windows', [])
        self._corners = result.get('corners', [])
        self._generated = True
    
    def get_doors(self, seed: int = 12345, **generation_params) -> List:
        """
        Get doors for this floor (generated lazily).
        
        Args:
            seed: Generation seed
            **generation_params: Parameters like door_density, edge_spacing
            
        Returns:
            List of door placements
        """
        if not self._generated:
            self.generate_elements(seed, **generation_params)
        return self._doors if self._doors is not None else []
    
    def get_windows(self, seed: int = 12345, **generation_params) -> List:
        """
        Get windows for this floor (generated lazily).
        
        Args:
            seed: Generation seed
            **generation_params: Parameters like window_density
            
        Returns:
            List of window placements
        """
        if not self._generated:
            self.generate_elements(seed, **generation_params)
        return self._windows if self._windows is not None else []
    
    def get_corners(self, seed: int = 12345, **generation_params) -> List:
        """
        Get corners for this floor (generated lazily).
        
        Args:
            seed: Generation seed
            **generation_params: Parameters like corner_size
            
        Returns:
            List of corners
        """
        if not self._generated:
            self.generate_elements(seed, **generation_params)
        return self._corners if self._corners is not None else []
    
    def clear_generated(self):
        """Clear generated elements to force regeneration on next access."""
        self._generated = False
        self._doors = None
        self._windows = None
        self._walls = None
        self._corners = None
