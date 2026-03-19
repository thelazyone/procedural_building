"""
Facade noise: random variance in facade (street-facing) edge positioning.

Applied per building: one random offset for all facades of that building.
- Row building: one facade (one edge on road) shifts
- Corner building: both facades shift by the same amount
"""

import math
import random
from typing import List, Optional, Set

from shapely.geometry import LineString, Polygon

from core.footprint import Point2D

MIN_SHARED_LENGTH = 0.1


def _get_geometry_length(geom) -> float:
    """Get total length of a geometry."""
    if geom is None or geom.is_empty:
        return 0.0
    if hasattr(geom, "length"):
        return geom.length
    if hasattr(geom, "geoms"):
        return sum(_get_geometry_length(g) for g in geom.geoms)
    return 0.0


def _find_road_edge_indices(
    footprint_verts: List[Point2D],
    block_boundary,
) -> Set[int]:
    """
    Find indices of footprint edges that touch the block boundary (road/facade).

    Returns the set of edge indices with overlap >= MIN_SHARED_LENGTH.
    """
    poly = Polygon(footprint_verts)
    if not poly.is_valid or poly.is_empty or block_boundary is None:
        return set()

    road_edges = set()
    n = len(footprint_verts)
    for i in range(n):
        a = footprint_verts[i]
        b = footprint_verts[(i + 1) % n]
        edge_line = LineString([a, b])
        shared = edge_line.intersection(block_boundary)
        if _get_geometry_length(shared) >= MIN_SHARED_LENGTH:
            road_edges.add(i)
    return road_edges


def _outward_normal(verts: List[Point2D], edge_idx: int) -> tuple:
    """
    Outward normal for edge (toward street) for CCW polygon.
    Returns (nx, ny) normalized, or (0, 0) if degenerate.
    """
    n = len(verts)
    a = verts[edge_idx]
    b = verts[(edge_idx + 1) % n]
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-9:
        return (0.0, 0.0)
    # Right of edge = outward for CCW
    return (dy / length, -dx / length)


def apply_facade_noise(
    footprint_vertices_list: List[List[Point2D]],
    seed: int,
    facade_noise: float = 0.0,
    block_vertices: Optional[List[Point2D]] = None,
) -> List[List[Point2D]]:
    """
    Apply random variance to facade (street-facing) edges of each building.

    One random offset per building, applied to ALL its facades:
    - Row building: one edge on road shifts
    - Corner building: both edges on road shift by the same amount

    Args:
        footprint_vertices_list: List of footprint vertex lists
        seed: Random seed for deterministic variance
        facade_noise: Max variance in meters (±facade_noise). 0 = no change
        block_vertices: Block boundary; required to identify facade edges

    Returns:
        List of footprint vertex lists (possibly modified)
    """
    if facade_noise <= 0 or block_vertices is None or len(block_vertices) < 3:
        return footprint_vertices_list

    block_poly = Polygon(block_vertices)
    if not block_poly.is_valid:
        block_poly = block_poly.buffer(0)
    block_boundary = block_poly.boundary

    result = []

    for footprint_idx, verts in enumerate(footprint_vertices_list):
        if len(verts) < 3:
            result.append(verts)
            continue

        road_edges = _find_road_edge_indices(verts, block_boundary)
        if not road_edges:
            result.append(verts)
            continue

        # One random offset for this building, applied to all its facades
        building_seed = abs(hash((seed, "facade_noise", footprint_idx)) % (2**31))
        rng = random.Random(building_seed)
        offset = rng.uniform(-facade_noise, facade_noise)
        if abs(offset) < 1e-6:
            result.append(verts)
            continue

        n = len(verts)
        # Accumulate shift per vertex from adjacent road edges
        vertex_shifts = [(0.0, 0.0)] * n
        for edge_idx in road_edges:
            nx, ny = _outward_normal(verts, edge_idx)
            if nx == 0 and ny == 0:
                continue
            # Edge connects vertex edge_idx to vertex (edge_idx+1)
            v1, v2 = edge_idx, (edge_idx + 1) % n
            shift_x = nx * offset
            shift_y = ny * offset
            vertex_shifts[v1] = (
                vertex_shifts[v1][0] + shift_x,
                vertex_shifts[v1][1] + shift_y,
            )
            vertex_shifts[v2] = (
                vertex_shifts[v2][0] + shift_x,
                vertex_shifts[v2][1] + shift_y,
            )

        new_verts = [
            (verts[i][0] + vertex_shifts[i][0], verts[i][1] + vertex_shifts[i][1])
            for i in range(n)
        ]
        poly = Polygon(new_verts)
        if poly.is_valid and not poly.is_empty:
            result.append(list(poly.exterior.coords[:-1]))
        else:
            result.append(verts)

    return result
