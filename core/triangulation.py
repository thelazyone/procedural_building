"""
2D footprint triangulation using Shapely (constrained Delaunay).

Used for OpenGL fills on simple polygons that may be concave. Unconstrained
Delaunay (shapely.ops.triangulate) can cross reflex vertices and must not be used.
"""

from typing import List, Tuple

from shapely import constrained_delaunay_triangles, is_valid, make_valid
from shapely.geometry import Polygon

from core.footprint import Point2D


def triangulate_simple_polygon(
    vertices: List[Point2D],
) -> List[Tuple[Point2D, Point2D, Point2D]]:
    """
    Triangulate a simple polygon (possibly concave). Exterior ring only.

    Falls back to a triangle fan if CDT is unavailable or fails.
    """
    n = len(vertices)
    if n < 3:
        return []
    if n == 3:
        return [(vertices[0], vertices[1], vertices[2])]

    poly = Polygon(vertices)
    if not is_valid(poly):
        poly = make_valid(poly)
    if poly.is_empty:
        return []

    if poly.geom_type == "Polygon":
        triangles = _triangles_from_polygon(poly)
        if triangles:
            return triangles
    elif poly.geom_type == "MultiPolygon":
        out: List[Tuple[Point2D, Point2D, Point2D]] = []
        for p in poly.geoms:
            out.extend(_triangles_from_polygon(p))
        if out:
            return out

    return _triangulate_convex_fan(vertices)


def _triangles_from_polygon(poly: Polygon) -> List[Tuple[Point2D, Point2D, Point2D]]:
    if poly.is_empty:
        return []
    try:
        gc = constrained_delaunay_triangles(poly)
    except Exception:
        return []
    if gc is None or gc.is_empty:
        return []
    result = []
    for g in getattr(gc, "geoms", []):
        if g.geom_type != "Polygon" or g.is_empty:
            continue
        coords = list(g.exterior.coords[:-1])
        if len(coords) == 3:
            result.append((tuple(coords[0]), tuple(coords[1]), tuple(coords[2])))
    return result


def _triangulate_convex_fan(
    vertices: List[Point2D],
) -> List[Tuple[Point2D, Point2D, Point2D]]:
    """Triangle fan from vertex 0 (correct only for convex polygons)."""
    n = len(vertices)
    if n < 3:
        return []
    v0 = vertices[0]
    return [(v0, vertices[i], vertices[i + 1]) for i in range(1, n - 1)]
