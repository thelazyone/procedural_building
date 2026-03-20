"""
Merge undersized adjacent footprints into lots that meet min_area.

Used after fine-grained subdivision (fragmentation > 1): join fragments by preferring
neighbors with the longest shared boundary to avoid thin serpentine chains.
"""

from typing import List, Optional, Tuple

import random
from shapely.geometry import Polygon
from shapely import is_valid, make_valid
from shapely.ops import unary_union

from core.footprint import Point2D
from core.footprint_cleanup import dedupe_consecutive_vertices
from blocks.filter_internal import get_geometry_length, MIN_SHARED_LENGTH
from blocks.subdivide import _exterior_ring

# Need a positive shared length to count as mergeable neighbor (real edge, not point)
MIN_MERGE_SHARED = max(MIN_SHARED_LENGTH, 0.08)

AREA_EPS = 1e-2


def _polygon_from_vertices(verts: List[Point2D]) -> Optional[Polygon]:
    if len(verts) < 3:
        return None
    p = Polygon(verts)
    if not is_valid(p):
        p = make_valid(p)
    if p.is_empty:
        return None
    if p.geom_type == "Polygon":
        return p
    if p.geom_type == "MultiPolygon":
        return max(p.geoms, key=lambda x: x.area, default=None)
    return None


def _block_boundary(block_vertices: List[Point2D]):
    bp = Polygon(block_vertices)
    if not bp.is_valid:
        bp = bp.buffer(0)
    return bp.boundary


def _road_shared_length(footprint_poly: Polygon, block_boundary) -> float:
    if footprint_poly is None or footprint_poly.is_empty or block_boundary is None:
        return 0.0
    fb = footprint_poly.boundary
    if fb is None:
        return 0.0
    return get_geometry_length(fb.intersection(block_boundary))


def _shared_boundary_length(a: Polygon, b: Polygon) -> float:
    if a is None or b is None or a.is_empty or b.is_empty:
        return 0.0
    ba, bb = a.boundary, b.boundary
    if ba is None or bb is None:
        return 0.0
    return get_geometry_length(ba.intersection(bb))


def _finalize_union_polygon(u) -> Optional[Polygon]:
    """
    Fix topology after unary_union (spikes, slivers) and normalize to one Polygon.
    """
    if u is None or u.is_empty:
        return None
    if not is_valid(u):
        u = make_valid(u)
    if u.is_empty:
        return None
    if u.geom_type == "MultiPolygon":
        return None
    p: Optional[Polygon] = None
    if u.geom_type == "Polygon":
        p = u
    elif u.geom_type == "GeometryCollection":
        polys = [g for g in u.geoms if g.geom_type == "Polygon" and not g.is_empty]
        if len(polys) != 1:
            return None
        p = polys[0]
    else:
        return None
    if p is None or p.is_empty:
        return None
    if not is_valid(p):
        p = make_valid(p)
    if p.is_empty or p.geom_type == "MultiPolygon":
        return None
    if p.geom_type != "Polygon":
        return None
    p = p.buffer(0)
    if p.is_empty:
        return None
    if p.geom_type == "MultiPolygon":
        p = max(p.geoms, key=lambda g: g.area, default=None)
    if p is None or p.geom_type != "Polygon" or p.is_empty:
        return None
    p = p.simplify(1e-8, preserve_topology=True)
    if p.is_empty:
        return None
    if p.geom_type == "MultiPolygon":
        p = max(p.geoms, key=lambda g: g.area, default=None)
    if p is None or p.geom_type != "Polygon" or p.is_empty:
        return None
    return p


def _try_union_pair(pi: Polygon, pj: Polygon) -> Optional[Polygon]:
    if pi is None or pj is None:
        return None
    u = unary_union([pi, pj])
    if u.is_empty:
        return None
    if u.geom_type == "MultiPolygon":
        return None
    if u.geom_type == "Polygon":
        return _finalize_union_polygon(u)
    if u.geom_type == "GeometryCollection":
        polys = [g for g in u.geoms if g.geom_type == "Polygon" and not g.is_empty]
        if len(polys) != 1:
            return None
        return _finalize_union_polygon(polys[0])
    return None


def _pick_fragment_index(
    polys: List[Polygon],
    under: List[int],
    block_boundary,
    rng: random.Random,
) -> int:
    """
    Prefer road-touching fragments, then smaller area; seeded tie-break.
    """
    scored: List[Tuple[float, float, float, int]] = []
    for i in under:
        road = _road_shared_length(polys[i], block_boundary)
        touches = 1.0 if road >= MIN_SHARED_LENGTH else 0.0
        area = polys[i].area
        scored.append((touches, -area, rng.random(), i))
    scored.sort(reverse=True)
    return scored[0][3]


def merge_footprints_to_min_area(
    footprint_vertices_list: List[List[Point2D]],
    block_vertices: List[Point2D],
    min_area: float,
    seed: int,
) -> List[List[Point2D]]:
    """
    Greedily merge adjacent footprints until each has area >= min_area.

    Each step: choose an undersized lot (road-touching first, then smallest),
    merge with the neighbor that has the largest total shared boundary length.
    Deterministic given ``seed`` (tie-breaks on equal shared length).

    Args:
        footprint_vertices_list: Fragment outlines from subdivision
        block_vertices: Block boundary (for road-touch preference)
        min_area: Target minimum lot area (m^2)
        seed: RNG seed for neighbor / tie ordering

    Returns:
        List of footprint vertex lists (same format as input)
    """
    if min_area <= 0:
        return [list(v) for v in footprint_vertices_list]

    verts = [list(v) for v in footprint_vertices_list if len(v) >= 3]
    if len(verts) <= 1:
        return verts

    rng = random.Random(seed)
    block_boundary = _block_boundary(block_vertices)

    max_steps = max(len(verts) * 20, 50)
    for _ in range(max_steps):
        polys = [_polygon_from_vertices(v) for v in verts]
        if any(p is None for p in polys):
            verts = [v for v, p in zip(verts, polys) if p is not None]
            if len(verts) <= 1:
                break
            continue

        under = [i for i, p in enumerate(polys) if p.area + AREA_EPS < min_area]
        if not under:
            break

        i = _pick_fragment_index(polys, under, block_boundary, rng)

        neighbors: List[Tuple[float, float, int]] = []
        for j in range(len(verts)):
            if j == i:
                continue
            L = _shared_boundary_length(polys[i], polys[j])
            if L < MIN_MERGE_SHARED:
                continue
            neighbors.append((L, rng.random(), j))

        if not neighbors:
            break

        neighbors.sort(key=lambda t: (-t[0], t[1]))
        merged_poly: Optional[Polygon] = None
        merge_j = -1
        for L, _, j in neighbors:
            mp = _try_union_pair(polys[i], polys[j])
            if mp is not None and mp.area > 0:
                merged_poly = mp
                merge_j = j
                break

        if merged_poly is None or merge_j < 0:
            break

        new_ring = dedupe_consecutive_vertices(_exterior_ring(merged_poly))
        if len(new_ring) < 3:
            break

        new_verts = [verts[k] for k in range(len(verts)) if k not in (i, merge_j)]
        new_verts.append(new_ring)
        verts = new_verts

    return verts
