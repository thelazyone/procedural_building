"""
Split concave footprints at the concave corner into two convex parts.

Uses a vertical or horizontal cut through the concave vertex.
Each part becomes a separate footprint (two buildings instead of one L-shaped).
"""

from typing import List

from shapely.geometry import Polygon, LineString
from shapely.ops import split

from core.footprint import Point2D


def _cross2d(o: Point2D, a: Point2D, b: Point2D) -> float:
    """Cross product (a-o) x (b-o) in 2D."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _signed_area(vertices: List[Point2D]) -> float:
    """Signed area; positive = CCW, negative = CW."""
    n = len(vertices)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1] - vertices[j][0] * vertices[i][1]
    return area / 2.0


def _is_concave(vertices: List[Point2D], i: int) -> bool:
    """True if vertex i is concave (interior angle > 180)."""
    n = len(vertices)
    if n < 3:
        return False
    prev_ = vertices[(i - 1) % n]
    curr = vertices[i]
    next_ = vertices[(i + 1) % n]
    cross = _cross2d(prev_, curr, next_)
    area = _signed_area(vertices)
    return (cross < 0) if area > 0 else (cross > 0)


def _split_with_line(
    poly: Polygon, vx: float, vy: float, vertical: bool, extent: float = 500.0
) -> List[List[Point2D]]:
    """Split polygon with vertical or horizontal line through (vx, vy)."""
    if vertical:
        line = LineString([(vx, vy - extent), (vx, vy + extent)])
    else:
        line = LineString([(vx - extent, vy), (vx + extent, vy)])
    try:
        result = split(poly, line)
    except Exception:
        return []
    parts = []
    if hasattr(result, "geoms"):
        for geom in result.geoms:
            if geom.geom_type == "Polygon" and not geom.is_empty:
                coords = list(geom.exterior.coords[:-1])
                if len(coords) >= 3:
                    parts.append(coords)
            elif geom.geom_type == "MultiPolygon":
                for p in geom.geoms:
                    if not p.is_empty:
                        coords = list(p.exterior.coords[:-1])
                        if len(coords) >= 3:
                            parts.append(coords)
    return parts


def split_concave_footprints(
    footprint_vertices_list: List[List[Point2D]],
) -> List[List[Point2D]]:
    """
    Split any concave footprints at the concave corner with a vertical or
    horizontal cut. Each part becomes a separate footprint (two buildings).

    Returns a new list of footprints, all convex.
    """
    result = []
    for verts in footprint_vertices_list:
        n = len(verts)
        if n < 3:
            result.append(verts)
            continue

        concave_idx = None
        for i in range(n):
            if _is_concave(verts, i):
                concave_idx = i
                break

        if concave_idx is None:
            result.append(verts)
            continue

        poly = Polygon(verts)
        if not poly.is_valid or poly.is_empty:
            result.append(verts)
            continue

        vx, vy = verts[concave_idx]
        # Try vertical cut first, then horizontal
        for vertical in (True, False):
            parts = _split_with_line(poly, vx, vy, vertical)
            if len(parts) >= 2:
                # Recursively split in case a part is still concave
                for part in parts:
                    result.extend(split_concave_footprints([part]))
                break
        else:
            result.append(verts)
    return result
