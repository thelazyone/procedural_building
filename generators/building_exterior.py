"""
Building exterior generator.

Generates the complete exterior structure from floor footprints:
- Wall segments
- Corners
- Windows
- Doors
"""

from typing import Any, Dict
from ..core.generator_base import GeneratorBase


class ExteriorGenerator(GeneratorBase):
    """
    Generates complete building exterior from floor footprints.
    """
    
    def generate(
        self,
        parent_context: Any,  # Building object
        seed: int,
        **params: Dict[str, Any]
    ) -> Any:
        """
        Generate exterior structure.
        
        Args:
            parent_context: Building object with floor footprints
            seed: Generation seed
            **params: Exterior parameters (style, window density, etc.)
            
        Returns:
            Exterior structure with walls, corners, windows, doors
        """
        # TODO: Implement exterior generation
        # 1. Generate walls from footprint edges
        # 2. Generate corners at vertices
        # 3. Generate windows on walls
        # 4. Generate doors/entrances
        pass
