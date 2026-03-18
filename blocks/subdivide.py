"""
Block subdivision using recursive longest-edge bisection.

Splits a block polygon into building footprints.
Algorithm: find longest edge, split with perpendicular line through random point (40-60%),
recurse until stopping conditions.
"""

import random
from typing import List, Tuple

from shapely.geometry import Polygon, LineString
from shapely.ops import split

from core.footprint import Point2D


def subdivide_block(
    vertices: List[Point2D],
    seed: int,
    min_area: float = 50.0,
    chance_no_divide: float = 0.05,
) -> List[List[Point2D]]:
    """
    Subdivide a block polygon into building footprints.

    Args:
        vertices: Block boundary as list of (x, y) vertices (CCW)
        seed: Random seed for deterministic subdivision
        min_area: Minimum lot area; controls subdivision depth
        chance_no_divide: Probability (0-1) a block stays undivided

    Returns:
        List of footprint vertex lists, each a building lot
    """
    rng = random.Random(seed)
    polygon = Polygon(vertices)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)  # Fix invalid polygon
    if polygon.is_empty or polygon.area < 0.5 * min_area:
        return []

    # Maybe keep block undivided
    if chance_no_divide > 0 and rng.random() < chance_no_divide:
        coords = list(polygon.exterior.coords[:-1])
        return [coords]

    result = _subdivide_recursive(polygon, min_area, rng)
    return result


def _subdivide_recursive(
    polygon: Polygon,
    min_area: float,
    rng: random.Random,
) -> List[List[Point2D]]:
    """Recursively subdivide polygon by longest edge."""
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
        coords = list(polygon.exterior.coords[:-1])
        return [coords]

    # Find longest edge
    coords = list(polygon.exterior.coords[:-1])
    n = len(coords)
    longest_len = -1
    longest_idx = 0

    for i in range(n):
        p1 = coords[i]
        p2 = coords[(i + 1) % n]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = (dx * dx + dy * dy) ** 0.5
        if length > longest_len:
            longest_len = length
            longest_idx = i

    if longest_len < 1e-6:
        coords = list(polygon.exterior.coords[:-1])
        return [coords]

    # Split point 40-60% along longest edge
    deviation = rng.uniform(0.4, 0.6)
    p1 = coords[longest_idx]
    p2 = coords[(longest_idx + 1) % n]
    mid_x = p1[0] + (p2[0] - p1[0]) * deviation
    mid_y = p1[1] + (p2[1] - p1[1]) * deviation

    # Perpendicular direction (normalized)
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1e-9:
        coords = list(polygon.exterior.coords[:-1])
        return [coords]
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
        coords = list(polygon.exterior.coords[:-1])
        return [coords]

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
        coords = list(polygon.exterior.coords[:-1])
        return [coords]

    # Recurse on each part
    output = []
    for part in parts:
        output.extend(_subdivide_recursive(part, min_area, rng))
    return output
