"""
Corner generator and Corner class.

Contains:
- Corner class: complete corner representation (placement + properties)
- CornerProperties: corner properties (size, style, etc.)
- CornerGenerator: generates corner properties for placed corners

The FloorGenerator handles placement logic, this handles the Corner class and its properties.
"""

from typing import Any, Dict
from core.generator_base import GeneratorBase
from core.footprint import Point2D
import random


class Corner:
    """
    Complete corner representation: placement + properties.
    
    Created by FloorGenerator by combining placement info with
    properties from CornerGenerator.
    """
    
    def __init__(
        self,
        vertex_idx: int,
        position: Point2D,
        prev_position: Point2D,
        next_position: Point2D,
        floor_idx: int,
        properties: 'CornerProperties'
    ):
        """
        Initialize corner.
        
        Args:
            vertex_idx: Index of the vertex this corner is at
            position: Position of the corner vertex
            prev_position: Position of previous vertex
            next_position: Position of next vertex
            floor_idx: Floor index
            properties: Corner properties (width, style, etc.)
        """
        self.vertex_idx = vertex_idx
        self.position = position
        self.prev_position = prev_position
        self.next_position = next_position
        self.floor_idx = floor_idx
        self.properties = properties
    
    @property
    def width(self) -> float:
        """Corner width."""
        return self.properties.width


class CornerProperties:
    """
    Properties for a corner (size, style, etc.).
    
    Corners are vertical elements at each vertex where two walls meet.
    """
    
    def __init__(
        self,
        width: float = 0.15,  # Width of corner piece
        style: str = "standard"
    ):
        """
        Initialize corner properties.
        
        Args:
            width: Width of corner element in meters
            style: Corner style (standard, ornate, rounded, etc.)
        """
        self.width = width
        self.style = style


class CornerGenerator(GeneratorBase):
    """
    Generates corner properties based on context and parameters.
    
    Corners are placed at each vertex of a floor's footprint.
    """
    
    def generate(
        self,
        parent_context: Any,  # Floor object
        seed: int,
        corner_idx: int = 0,
        **params: Dict[str, Any]
    ) -> CornerProperties:
        """
        Generate properties for a corner.
        
        Args:
            parent_context: Context information (floor, building style, etc.)
            seed: Generation seed
            corner_idx: Index of this corner
            **params: Override parameters (width, style, etc.)
            
        Returns:
            CornerProperties object
        """
        rng = random.Random(seed)
        
        # Extract only the relevant corner parameters
        corner_params = {}
        if 'corner_size' in params:  # UI uses 'corner_size'
            corner_params['width'] = params['corner_size']
        elif 'width' in params:
            corner_params['width'] = params['width']
        if 'style' in params:
            corner_params['style'] = params['style']
        
        # Let CornerProperties handle all defaults
        return CornerProperties(**corner_params)
