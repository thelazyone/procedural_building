"""
Filter out footprints that don't share an edge with the block boundary.

Internal footprints (fully surrounded by other footprints) are removed,
creating courtyards / inside spaces.
"""

from typing import List

from shapely.geometry import Polygon

from core.footprint import Point2D

# Minimum shared edge length to consider footprint "on the block" (meters)
MIN_SHARED_LENGTH = 0.1


def filter_footprints_touching_block(
    block_vertices: List[Point2D],
    footprint_vertices_list: List[List[Point2D]],
) -> List[List[Point2D]]:
    """
    Keep only footprints that share at least one edge with the block boundary.

    Footprints with no edge on the block perimeter (fully internal) are removed.

    Args:
        block_vertices: Block boundary vertices
        footprint_vertices_list: List of footprint vertex lists

    Returns:
        Filtered list of footprint vertex lists
    """
    block_poly = Polygon(block_vertices)
    if not block_poly.is_valid:
        block_poly = block_poly.buffer(0)
    block_boundary = block_poly.boundary
    if block_boundary is None:
        return footprint_vertices_list

    result = []
    for footprint_vertices in footprint_vertices_list:
        footprint_poly = Polygon(footprint_vertices)
        if not footprint_poly.is_valid or footprint_poly.is_empty:
            continue
        footprint_boundary = footprint_poly.boundary
        if footprint_boundary is None:
            continue

        shared = footprint_boundary.intersection(block_boundary)
        if shared.is_empty:
            continue
        # Check if they share a meaningful edge (not just a point)
        length = get_geometry_length(shared)
        if length >= MIN_SHARED_LENGTH:
            result.append(footprint_vertices)

    return result


def get_geometry_length(geom) -> float:
    """Get total length of a geometry (LineString, MultiLineString, etc.)."""
    if geom is None or geom.is_empty:
        return 0.0
    if hasattr(geom, "length"):
        return geom.length
    if hasattr(geom, "geoms"):
        return sum(get_geometry_length(g) for g in geom.geoms)
    return 0.0
