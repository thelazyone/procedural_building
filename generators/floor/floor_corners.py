"""
Corner placement logic for floors.

Contains the logic for determining WHERE corners should be placed on a floor.
Corners are placed at each vertex of the floor's footprint.
"""

from typing import List
from core.floor import Floor
from generators.corner import Corner, CornerGenerator


def generate_corners(
    floor: Floor,
    seed: int,
    **params
) -> List[Corner]:
    """
    Generate corners for a floor at all vertices.
    
    This function places corners at each vertex of the floor's footprint
    and creates Corner objects with properties from CornerGenerator.
    
    Args:
        floor: Floor object to generate corners for
        seed: Generation seed
        **params: Additional parameters passed to CornerGenerator
        
    Returns:
        List of Corner objects with placement and properties
    """
    footprint = floor.footprint
    vertices = footprint.get_vertices()
    num_vertices = len(vertices)
    
    corners = []
    corner_generator = CornerGenerator()
    
    for i, vertex in enumerate(vertices):
        prev_vertex = vertices[(i - 1) % num_vertices]
        next_vertex = vertices[(i + 1) % num_vertices]
        
        # Generate corner properties
        corner_seed = hash((seed, "corner", i)) % (2**31)
        corner_props = corner_generator.generate(
            parent_context=floor,
            seed=corner_seed,
            corner_idx=i,
            **params
        )
        
        # Create complete Corner object
        corner = Corner(
            vertex_idx=i,
            position=vertex,
            prev_position=prev_vertex,
            next_position=next_vertex,
            floor_idx=floor.floor_idx,
            properties=corner_props
        )
        corners.append(corner)
    
    return corners
