"""
Block subdivision using recursive longest-edge bisection.

Splits a block polygon into building footprints.
Algorithm: pick a split edge among the near-longest edges (seed-weighted by length),
split with a perpendicular through a random point along that edge, recurse.

Pure longest-edge + a tight split band (40–60%) made the first cuts almost
shape-determined; edge pool + wider t range keeps lots balanced but varies with seed.
"""

import random
from typing import List, Optional, Tuple

from shapely.geometry import Polygon, LineString
from shapely import is_valid, make_valid
from shapely.ops import split

from core.footprint import Point2D

# Edges with length >= EDGE_POOL_RATIO * max_length are candidates for the split line.
# <1.0 lets equivalent long sides (e.g. both long sides of a rectangle) compete by seed.
EDGE_POOL_RATIO = 0.82

# Split point along chosen edge: uniform in [SPLIT_T_LO, SPLIT_T_HI] (avoid vertices).
SPLIT_T_LO = 0.12
SPLIT_T_HI = 0.88


def _pick_edge_index_weighted(
    coords: List[Point2D],
    rng: random.Random,
) -> Optional[Tuple[int, float]]:
    """
    Choose edge index to split along: pool of near-longest edges, weighted by length.

    Returns (edge_start_index, edge_length) or None if degenerate.
    """
    n = len(coords)
    if n < 3:
        return None
    lengths: List[Tuple[int, float]] = []
    max_len = 0.0
    for i in range(n):
        p1 = coords[i]
        p2 = coords[(i + 1) % n]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        L = (dx * dx + dy * dy) ** 0.5
        if L > 1e-9:
            lengths.append((i, L))
            if L > max_len:
                max_len = L
    if not lengths or max_len < 1e-6:
        return None
    threshold = max_len * EDGE_POOL_RATIO
    candidates = [(i, L) for i, L in lengths if L >= threshold]
    if not candidates:
        candidates = lengths
    total_w = sum(L for _, L in candidates)
    if total_w < 1e-12:
        return None
    r = rng.uniform(0.0, total_w)
    acc = 0.0
    for i, L in candidates:
        acc += L
        if r <= acc:
            return (i, L)
    return (candidates[-1][0], candidates[-1][1])


def _as_single_polygon(geom) -> Optional[Polygon]:
    """Reduce to one Polygon for exterior-based splitting (largest part if MultiPolygon)."""
    if geom is None or geom.is_empty:
        return None
    if geom.geom_type == "Polygon":
        return geom
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda p: p.area, default=None)
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type == "Polygon" and not g.is_empty]
        if not polys:
            return None
        return max(polys, key=lambda p: p.area)
    return None


def _exterior_ring(poly: Polygon) -> List[Point2D]:
    """Exterior vertices only; fix invalid geometry from split operations."""
    if not is_valid(poly):
        fixed = make_valid(poly)
        if fixed.is_empty:
            return []
        if fixed.geom_type == "Polygon":
            poly = fixed
        elif fixed.geom_type == "MultiPolygon":
            poly = max(fixed.geoms, key=lambda p: p.area, default=None)
            if poly is None or poly.is_empty:
                return []
        else:
            return []
    if poly.is_empty:
        return []
    return list(poly.exterior.coords[:-1])


def subdivide_block(
    vertices: List[Point2D],
    seed: int,
    min_area: float = 50.0,
    chance_no_divide: float = 0.05,
    fragmentation: float = 1.0,
) -> List[List[Point2D]]:
    """
    Subdivide a block polygon into building footprints.

    Args:
        vertices: Block boundary as list of (x, y) vertices (CCW)
        seed: Random seed for deterministic subdivision
        min_area: Target minimum lot area after any merge step; also sets coarsest
            stop when fragmentation is 1 (see fragmentation).
        chance_no_divide: Probability (0-1) a block stays undivided
        fragmentation: >= 1. Subdivision uses min_area / fragmentation as the
            effective minimum size, producing more fragments (merged later).

    Returns:
        List of footprint vertex lists, each a building lot
    """
    rng = random.Random(seed)
    frag = max(float(fragmentation), 1.0)
    min_for_split = min_area / frag

    polygon = Polygon(vertices)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)  # Fix invalid polygon
    polygon = _as_single_polygon(polygon)
    if polygon is None or polygon.is_empty or polygon.area < 0.5 * min_for_split:
        return []

    # Maybe keep block undivided
    if chance_no_divide > 0 and rng.random() < chance_no_divide:
        coords = _exterior_ring(polygon)
        return [coords] if coords else []

    result = _subdivide_recursive(polygon, min_for_split, rng)
    return result


def _subdivide_recursive(
    polygon: Polygon,
    min_area: float,
    rng: random.Random,
) -> List[List[Point2D]]:
    """Recursively subdivide polygon by longest edge."""
    polygon = _as_single_polygon(polygon)
    if polygon is None or polygon.is_empty:
        return []
    area = polygon.area
    if area < 0.5 * min_area:
        return []

    # Shape index: area / perimeter^2. Too skinny if < 0.02
    # (0.04 was too strict for L-shaped fragments with long perimeter)
    perimeter = polygon.length
    if perimeter < 1e-6:
        return []
    shape_index = area / (perimeter * perimeter)
    if shape_index < 0.02:
        return []

    if area < 2 * min_area:
        coords = _exterior_ring(polygon)
        return [coords] if coords else []

    coords = _exterior_ring(polygon)
    if len(coords) < 3:
        return []
    n = len(coords)

    picked = _pick_edge_index_weighted(coords, rng)
    if picked is None:
        coords = _exterior_ring(polygon)
        return [coords] if coords else []
    longest_idx, longest_len = picked

    if longest_len < 1e-6:
        coords = _exterior_ring(polygon)
        return [coords] if coords else []

    # Split point along chosen edge (seed-driven, avoids extreme slivers at corners)
    t = rng.uniform(SPLIT_T_LO, SPLIT_T_HI)
    p1 = coords[longest_idx]
    p2 = coords[(longest_idx + 1) % n]
    mid_x = p1[0] + (p2[0] - p1[0]) * t
    mid_y = p1[1] + (p2[1] - p1[1]) * t

    # Perpendicular direction (normalized)
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1e-9:
        coords = _exterior_ring(polygon)
        return [coords] if coords else []
    perp_x = -dy / length
    perp_y = dx / length

    # Extend line 100 units each way
    extent = 100.0
    line_start = (mid_x - perp_x * extent, mid_y - perp_y * extent)
    line_end = (mid_x + perp_x * extent, mid_y + perp_y * extent)
    splitter = LineString([line_start, line_end])

    try:
        result = split(polygon, splitter)
    except Exception:
        coords = _exterior_ring(polygon)
        return [coords] if coords else []

    # result is GeometryCollection; extract polygons
    parts = []
    if hasattr(result, 'geoms'):
        for geom in result.geoms:
            if geom.geom_type == 'Polygon' and not geom.is_empty:
                parts.append(geom)
            elif geom.geom_type == 'MultiPolygon':
                for p in geom.geoms:
                    if not p.is_empty:
                        parts.append(p)
    elif result.geom_type == 'Polygon':
        parts = [result]

    if len(parts) < 2:
        coords = _exterior_ring(polygon)
        return [coords] if coords else []

    # Recurse on each part
    output = []
    for part in parts:
        if not part.is_valid:
            part = make_valid(part)
        if part.geom_type == "Polygon" and not part.is_empty:
            output.extend(_subdivide_recursive(part, min_area, rng))
        elif part.geom_type == "MultiPolygon":
            for p in part.geoms:
                if not p.is_empty:
                    output.extend(_subdivide_recursive(p, min_area, rng))
    return output
