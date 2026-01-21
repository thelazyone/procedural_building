"""
Coordinate system conversion utilities.

Handles conversion between Z-up (internal) and Y-up (some engines) coordinates.
"""

from typing import Tuple

Point3D = Tuple[float, float, float]


class CoordinateSystem:
    """
    Manages coordinate system conversions.
    
    Internal representation uses Z-up (X-right, Y-forward, Z-up).
    Can convert to Y-up (X-right, Y-up, Z-forward) for engines that need it.
    """
    
    def __init__(self, up_axis: str = "Z"):
        """
        Initialize coordinate system.
        
        Args:
            up_axis: "Z" for Z-up (default), "Y" for Y-up
        """
        if up_axis not in ["Z", "Y"]:
            raise ValueError("up_axis must be 'Z' or 'Y'")
        self.up_axis = up_axis
    
    def to_internal(self, point: Point3D) -> Point3D:
        """
        Convert point from current coordinate system to internal (Z-up).
        
        Args:
            point: (x, y, z) in current coordinate system
            
        Returns:
            (x, y, z) in Z-up coordinates
        """
        if self.up_axis == "Z":
            return point  # Already Z-up
        else:
            # Y-up to Z-up: (x, y, z) -> (x, z, -y)
            x, y, z = point
            return (x, z, -y)
    
    def from_internal(self, point: Point3D) -> Point3D:
        """
        Convert point from internal (Z-up) to current coordinate system.
        
        Args:
            point: (x, y, z) in Z-up coordinates
            
        Returns:
            (x, y, z) in current coordinate system
        """
        if self.up_axis == "Z":
            return point  # Already Z-up
        else:
            # Z-up to Y-up: (x, y, z) -> (x, -z, y)
            x, y, z = point
            return (x, -z, y)
    
    def convert_points(self, points: list[Point3D], from_z_up: bool = True) -> list[Point3D]:
        """
        Convert a list of points.
        
        Args:
            points: List of 3D points
            from_z_up: If True, converts from Z-up to current system.
                      If False, converts from current system to Z-up.
                      
        Returns:
            List of converted points
        """
        converter = self.from_internal if from_z_up else self.to_internal
        return [converter(p) for p in points]


# Global coordinate system instance
_coord_system = CoordinateSystem("Z")


def set_up_axis(axis: str):
    """
    Set the global up axis for coordinate conversions.
    
    Args:
        axis: "Z" or "Y"
    """
    global _coord_system
    _coord_system = CoordinateSystem(axis)


def get_coordinate_system() -> CoordinateSystem:
    """Get the global coordinate system instance."""
    return _coord_system
