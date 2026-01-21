"""
Footprint utilities wrapper around Shapely.

Provides a clean interface for working with non-convex, non-intersecting footprints.
A footprint represents the 2D floor plan outline of a building floor.
"""

from typing import List, Tuple
from shapely.geometry import Polygon as ShapelyPolygon
from shapely import is_valid, make_valid

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
        if len(vertices) < 3:
            raise ValueError("Footprint must have at least 3 vertices")
        
        # Create Shapely polygon
        self._polygon = ShapelyPolygon(vertices)
        
        # Validate and fix if needed
        if not is_valid(self._polygon):
            self._polygon = make_valid(self._polygon)
            if not is_valid(self._polygon):
                raise ValueError("Could not create valid footprint from vertices")
        
        # Store original vertices in normalized order (CCW exterior)
        self._vertices = list(self._polygon.exterior.coords[:-1])  # Exclude duplicate last point
    
    def get_vertices(self) -> List[Point2D]:
        """Get footprint vertices in order (CCW)."""
        return self._vertices.copy()
    
    def get_edges(self) -> List[Tuple[Point2D, Point2D]]:
        """Get footprint edges as (start, end) pairs."""
        edges = []
        vertices = self._vertices
        for i in range(len(vertices)):
            start = vertices[i]
            end = vertices[(i + 1) % len(vertices)]
            edges.append((start, end))
        return edges
    
    def is_valid(self) -> bool:
        """Check if footprint is valid (no self-intersection)."""
        return is_valid(self._polygon)
    
    def contains_point(self, point: Point2D) -> bool:
        """Check if point is inside footprint."""
        return self._polygon.contains(ShapelyPolygon([point]))
    
    def area(self) -> float:
        """Calculate footprint area in square meters."""
        return self._polygon.area
    
    def perimeter(self) -> float:
        """Calculate footprint perimeter in meters."""
        return self._polygon.length
    
    @property
    def polygon(self) -> ShapelyPolygon:
        """Access underlying Shapely polygon for advanced operations."""
        return self._polygon
