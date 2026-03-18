"""
Add gaps between buildings by shifting one edge orthogonal to the road inward.

Each building independently shifts one edge that is orthogonal to the road:
- Single-road building: pick one of the two side edges (both orthogonal to road)
- Corner building: pick one of the two inside edges (each orthogonal to a road)
"""

import random
from typing import List, Optional, Set

from shapely.geometry import LineString, Polygon

from core.footprint import Point2D

MIN_SHARED_LENGTH = 0.1


def _get_geometry_length(geom) -> float:
    """Get total length of a geometry (LineString, MultiLineString, etc.)."""
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
    Find indices of footprint edges that touch the block boundary (road).

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


def _edge_length(verts: List[Point2D], edge_idx: int) -> float:
    """Length of edge at edge_idx."""
    n = len(verts)
    a = verts[edge_idx]
    b = verts[(edge_idx + 1) % n]
    return ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5


def _find_orthogonal_edge_to_shift(
    footprint_verts: List[Point2D],
    road_edge_indices: Set[int],
    rng: random.Random,
) -> Optional[int]:
    """
    Find one edge orthogonal to the road to shift inward.

    - Single-road (1 edge on road): pick one of the two adjacent edges (random)
    - Corner (2 edges on road): pick the shorter of the two non-road edges
    """
    n = len(footprint_verts)
    if not road_edge_indices:
        return None

    if len(road_edge_indices) == 1:
        # Single road: the two edges adjacent to the road edge (orthogonal to it)
        road_idx = next(iter(road_edge_indices))
        prev_idx = (road_idx - 1) % n
        next_idx = (road_idx + 1) % n
        candidates = [prev_idx, next_idx]
        return rng.choice(candidates)
    else:
        # Corner: pick the shorter of the two non-road edges
        candidates = [i for i in range(n) if i not in road_edge_indices]
        if not candidates:
            return None
        return min(candidates, key=lambda i: _edge_length(footprint_verts, i))


def _shift_edge_inward(
    verts: List[Point2D],
    edge_idx: int,
    gap_size: float,
    footprint_centroid,
) -> List[Point2D]:
    """
    Shift the edge at edge_idx inward by gap_size.

    Inward = toward footprint centroid (shrinks the building, creates gap).
    """
    n = len(verts)
    a = verts[edge_idx]
    b = verts[(edge_idx + 1) % n]
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    edge_vec = (b[0] - a[0], b[1] - a[1])
    perp_ccw = (-edge_vec[1], edge_vec[0])
    perp_cw = (edge_vec[1], -edge_vec[0])
    cx, cy = footprint_centroid.x, footprint_centroid.y
    to_centroid = (cx - mid[0], cy - mid[1])
    dot_ccw = perp_ccw[0] * to_centroid[0] + perp_ccw[1] * to_centroid[1]
    norm = perp_ccw if dot_ccw > 0 else perp_cw
    length = (norm[0] ** 2 + norm[1] ** 2) ** 0.5
    if length < 1e-9:
        return verts
    norm = (norm[0] / length, norm[1] / length)
    a_new = (a[0] + gap_size * norm[0], a[1] + gap_size * norm[1])
    b_new = (b[0] + gap_size * norm[0], b[1] + gap_size * norm[1])
    new_verts = list(verts)
    new_verts[edge_idx] = a_new
    new_verts[(edge_idx + 1) % n] = b_new
    return new_verts


def apply_gaps(
    footprint_vertices_list: List[List[Point2D]],
    seed: int,
    gap_chance: float = 0.2,
    gap_size: float = 2.0,
    block_vertices: Optional[List[Point2D]] = None,
) -> List[List[Point2D]]:
    """
    Shift one edge orthogonal to the road inward with probability gap_chance.

    - Single-road building: pick one of the two side edges (orthogonal to road)
    - Corner building: pick one of the two inside edges (each orthogonal to a road)

    Args:
        footprint_vertices_list: List of footprint vertex lists
        seed: Random seed
        gap_chance: 0 = no gaps, 1 = all buildings shift one orthogonal edge
        gap_size: Distance to shift the edge inward
        block_vertices: Block boundary; required for road-aware logic

    Returns:
        List of footprint vertex lists (possibly modified)
    """
    if gap_chance <= 0 or gap_size <= 0:
        return footprint_vertices_list

    if block_vertices is None or len(block_vertices) < 3:
        return footprint_vertices_list

    block_poly = Polygon(block_vertices)
    if not block_poly.is_valid:
        block_poly = block_poly.buffer(0)
    block_boundary = block_poly.boundary

    rng = random.Random(seed)
    result = []

    for verts in footprint_vertices_list:
        if len(verts) < 3:
            result.append(verts)
            continue

        if rng.random() >= gap_chance:
            result.append(verts)
            continue

        road_edges = _find_road_edge_indices(verts, block_boundary)
        edge_idx = _find_orthogonal_edge_to_shift(verts, road_edges, rng)
        if edge_idx is None:
            result.append(verts)
            continue

        footprint_centroid = Polygon(verts).centroid
        new_verts = _shift_edge_inward(verts, edge_idx, gap_size, footprint_centroid)
        poly = Polygon(new_verts)
        if poly.is_valid and not poly.is_empty:
            result.append(list(poly.exterior.coords[:-1]))
        else:
            result.append(verts)

    return result
