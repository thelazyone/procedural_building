"""
Building data structure and main interface.

A building is defined by:
- Multiple floors, each with footprint and height
- Building-level parameters (style, etc.)
- Hierarchical lazy generation of exterior elements
"""

from typing import List, Optional, Dict, Any, Union
from core.footprint import Footprint, Point2D
from generators.floor.floor import Floor


class Building:
    """
    Main building structure.
    
    Represents a multi-floor building with lazy generation of all sub-elements.
    """
    
    def __init__(
        self,
        floors: Union[List[Floor], List[List[Point2D]]],
        seed: int,
        floor_heights: Optional[List[float]] = None,
        default_floor_height: float = 3.0,
        **params
    ):
        """
        Initialize building.
        
        Args:
            floors: Either list of Floor objects, or list of vertex lists (one per floor)
            seed: Seed for deterministic generation
            floor_heights: Optional list of heights per floor (if floors are vertex lists)
            default_floor_height: Default height if floor_heights not provided
            **params: Additional building parameters (style, material, etc.)
        """
        self.seed = seed
        self.params = params
        
        # Initialize floors
        if isinstance(floors[0], Floor):
            self.floors = floors
        else:
            # Create Floor objects from vertex lists
            if floor_heights is None:
                floor_heights = [default_floor_height] * len(floors)
            elif len(floor_heights) != len(floors):
                raise ValueError("floor_heights length must match number of floors")
            
            self.floors = [
                Floor.from_vertices(vertices, height=floor_heights[i], floor_idx=i)
                for i, vertices in enumerate(floors)
            ]
        
        # Calculate cumulative heights for easy Z positioning
        self._cumulative_heights = [0.0]
        for floor in self.floors:
            self._cumulative_heights.append(self._cumulative_heights[-1] + floor.height)
        
        # Lazy caches
        self._walls: Optional[List] = None
        self._exterior: Optional[Any] = None
    
    @property
    def num_floors(self) -> int:
        """Number of floors in building."""
        return len(self.floors)
    
    def get_floor(self, floor_idx: int) -> Floor:
        """Get floor object for specific floor (0-indexed from bottom)."""
        return self.floors[floor_idx]
    
    def get_floor_z_base(self, floor_idx: int) -> float:
        """Get base Z coordinate for specific floor."""
        return self._cumulative_heights[floor_idx]
    
    def get_floor_z_top(self, floor_idx: int) -> float:
        """Get top Z coordinate for specific floor."""
        return self._cumulative_heights[floor_idx + 1]
    
    def get_total_height(self) -> float:
        """Get total building height in meters."""
        return self._cumulative_heights[-1]
    
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
