"""
Footprint ring cleanup: dedupe vertices and remove collinear points.

Used after subdivision/merge/noise and before facade adjacency (front/back/occlusion).
"""

import math
from typing import List

from shapely import is_valid, make_valid
from shapely.geometry import Polygon

from core.footprint import Point2D

# Squared distance below which consecutive vertices are merged
_DEDUPE_EPS_SQ = 1e-10


def dedupe_consecutive_vertices(vertices: List[Point2D]) -> List[Point2D]:
    """Remove consecutive duplicate (or nearly duplicate) points on the ring."""
    if len(vertices) < 2:
        return list(vertices)
    out: List[Point2D] = [vertices[0]]
    for x, y in vertices[1:]:
        px, py = out[-1]
        if (x - px) ** 2 + (y - py) ** 2 > _DEDUPE_EPS_SQ:
            out.append((float(x), float(y)))
    if (
        len(out) >= 2
        and (out[0][0] - out[-1][0]) ** 2 + (out[0][1] - out[-1][1]) ** 2
        <= _DEDUPE_EPS_SQ
    ):
        out.pop()
    return out


def remove_collinear_vertices(
    vertices: List[Point2D],
    angle_tolerance_deg: float = 0.1,
) -> List[Point2D]:
    """
    Drop vertices that lie on the straight segment between previous and next.

    Uses turning angle at curr between edges (prev→curr) and (curr→next);
    ~0 means same direction (180° interior corner flattened to a line).
    """
    tol = math.radians(angle_tolerance_deg)
    v = list(vertices)
    original = list(vertices)

    def is_straight(prev: Point2D, curr: Point2D, nxt: Point2D) -> bool:
        vx1 = curr[0] - prev[0]
        vy1 = curr[1] - prev[1]
        vx2 = nxt[0] - curr[0]
        vy2 = nxt[1] - curr[1]
        len1_sq = vx1 * vx1 + vy1 * vy1
        len2_sq = vx2 * vx2 + vy2 * vy2
        if len1_sq < 1e-20 or len2_sq < 1e-20:
            return True
        cross = vx1 * vy2 - vy1 * vx2
        dot = vx1 * vx2 + vy1 * vy2
        turn = math.atan2(cross, dot)
        return abs(turn) < tol

    while len(v) >= 4:
        n = len(v)
        new_v: List[Point2D] = []
        removed_any = False
        for i in range(n):
            prev = v[(i - 1) % n]
            curr = v[i]
            nxt = v[(i + 1) % n]
            if is_straight(prev, curr, nxt):
                removed_any = True
                continue
            new_v.append(curr)
        if not removed_any:
            break
        if len(new_v) < 3:
            return original
        v = new_v
    return v


def prepare_footprint_for_adjacency(
    vertices: List[Point2D],
    angle_tolerance_deg: float = 0.1,
) -> List[Point2D]:
    """
    Dedupe, remove collinear points, then take a clean Shapely exterior ring.

    Keeps topology valid for facade edge indexing; falls back to best-effort list
    if the polygon cannot be made valid.
    """
    if len(vertices) < 3:
        return list(vertices)

    v = dedupe_consecutive_vertices(vertices)
    v = remove_collinear_vertices(v, angle_tolerance_deg=angle_tolerance_deg)
    if len(v) < 3:
        return dedupe_consecutive_vertices(list(vertices))

    poly = Polygon(v)
    if not is_valid(poly):
        poly = make_valid(poly)
    if poly.is_empty:
        return v if len(v) >= 3 else list(vertices)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area, default=None)
    if poly is None or poly.geom_type != "Polygon":
        return v if len(v) >= 3 else list(vertices)

    simplified = poly.simplify(1e-9, preserve_topology=True)
    if simplified.geom_type == "Polygon" and not simplified.is_empty:
        poly = simplified
    if poly.is_empty or not is_valid(poly):
        poly = make_valid(poly)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area, default=None)
    if poly is None or poly.geom_type != "Polygon" or poly.is_empty:
        return v

    return list(poly.exterior.coords[:-1])
