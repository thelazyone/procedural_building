"""
Door generator.

Generates doors/entrances on wall segments (typically ground floor).
"""

from typing import Any, Dict, List
from ..core.generator_base import GeneratorBase
from ..core.footprint import Point2D


class Door:
    """
    Represents a door/entrance on a wall segment.
    
    Doors are typically on ground floor exterior walls.
    """
    
    def __init__(
        self,
        position: float,  # Position along wall segment (0.0 to 1.0)
        wall_start: Point2D,
        wall_end: Point2D,
        floor_idx: int,
        floor_height: float,
        width: float = 1.0,
        height: float = 2.1,
        is_main_entrance: bool = False
    ):
        """
        Initialize door.
        
        Args:
            position: Normalized position along wall (0.0 = start, 1.0 = end)
            wall_start: Wall segment start point
            wall_end: Wall segment end point
            floor_idx: Floor index (typically 0 for entrances)
            floor_height: Floor height in meters
            width: Door width in meters
            height: Door height in meters
            is_main_entrance: Whether this is the main building entrance
        """
        self.position = position
        self.wall_start = wall_start
        self.wall_end = wall_end
        self.floor_idx = floor_idx
        self.floor_height = floor_height
        self.width = width
        self.height = height
        self.is_main_entrance = is_main_entrance
    
    def get_world_position(self) -> Point2D:
        """Calculate actual world (x, y) position of door center."""
        x = self.wall_start[0] + (self.wall_end[0] - self.wall_start[0]) * self.position
        y = self.wall_start[1] + (self.wall_end[1] - self.wall_start[1]) * self.position
        return (x, y)
    
    def get_z_position(self) -> float:
        """Calculate Z position (height) of door center."""
        return self.floor_idx * self.floor_height + self.height / 2


class DoorGenerator(GeneratorBase):
    """
    Generates doors on wall segments.
    """
    
    def generate(
        self,
        parent_context: Any,  # WallSegment object
        seed: int,
        num_doors: int = 0,
        placement: str = "auto",  # "auto", "center", "edges"
        **params: Dict[str, Any]
    ) -> List[Door]:
        """
        Generate doors on a wall segment.
        
        Args:
            parent_context: WallSegment object
            seed: Generation seed
            num_doors: Number of doors to place (0 = auto-determine)
            placement: Placement strategy
            **params: Door parameters (width, height, style, etc.)
            
        Returns:
            List of Door objects
        """
        # TODO: Implement door generation
        # Ground floor typically gets 1+ entrances
        # Use seed for deterministic placement
        # Avoid conflicts with windows
        pass
