"""
Corner generator.

Generates corner properties for building edges where walls meet.
"""

from typing import Any, Dict
from core.generator_base import GeneratorBase
import random


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
