"""
Footprint utilities wrapper around Shapely.

Provides a clean interface for working with non-convex, non-intersecting footprints.
A footprint represents the 2D floor plan outline of a building floor.
"""

from typing import List, Tuple

Point2D = Tuple[float, float]


class Footprint:
    """
    Wrapper around Shapely polygon with additional utilities.
    
    Represents a 2D non-convex, non-intersecting footprint (floor outline).
    """
    
    def __init__(self, vertices: List[Point2D]):
        """
        Initialize footprint from vertex list.
        
        Args:
            vertices: List of (x, y) tuples defining the footprint boundary.
                     Should be ordered (CCW or CW, will be normalized).
        """
        # TODO: Initialize Shapely polygon
        # TODO: Validate non-intersecting
        # TODO: Normalize orientation
        pass
    
    def get_vertices(self) -> List[Point2D]:
        """Get footprint vertices in order."""
        pass
    
    def get_edges(self) -> List[Tuple[Point2D, Point2D]]:
        """Get footprint edges as (start, end) pairs."""
        pass
    
    def is_valid(self) -> bool:
        """Check if footprint is valid (no self-intersection)."""
        pass
    
    def contains_point(self, point: Point2D) -> bool:
        """Check if point is inside footprint."""
        pass
    
    def area(self) -> float:
        """Calculate footprint area."""
        pass
    
    def perimeter(self) -> float:
        """Calculate footprint perimeter."""
        pass
