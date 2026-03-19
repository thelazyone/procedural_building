"""
Compute facade definition from block context.

Given block boundary and all footprints, classifies each footprint edge as:
- FRONT: touches block boundary (main road)
- OCCLUSION: touches another building footprint
- BACK: neither (backroad / interior-facing)

When a building edge is partially touching another, the edge is split into
segments: the touching part becomes OCCLUSION, the free part keeps its base
kind (FRONT or BACK). The footprint shape stays the same; only the segment
classification differs for the building generator.
"""

from typing import List, Optional, Tuple

from shapely.geometry import LineString, Point, Polygon

from core.footprint import Point2D
from core.facade import (
    FacadeDefinition,
    FacadeSegment,
    FacadeSegmentKind,
)

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


def _edge_touches_geometry(
    a: Point2D, b: Point2D, geometry, min_length: float = MIN_SHARED_LENGTH
) -> bool:
    """True if edge a-b overlaps geometry by at least min_length."""
    edge_line = LineString([a, b])
    shared = edge_line.intersection(geometry)
    return _get_geometry_length(shared) >= min_length


def _point_to_param(a: Point2D, b: Point2D, p: Point2D) -> float:
    """
    Map a point on the line a-b to parametric coordinate t in [0,1].
    Returns t such that p ≈ a + t*(b-a). Clamped to [0,1].
    """
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-18:
        return 0.0
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length_sq
    return max(0.0, min(1.0, t))


def _get_occlusion_intervals(
    a: Point2D, b: Point2D, other_data: List[Tuple],
) -> List[Tuple[float, float, float]]:
    """
    Find parametric intervals [t_lo, t_hi] on edge a-b where it overlaps
    other footprints. other_data = [(boundary, height), ...] per other footprint.
    Returns [(t_lo, t_hi, occlusion_height), ...] merged; when intervals overlap,
    takes max height (occlusion up to the taller building).
    """
    edge_line = LineString([a, b])
    intervals = []

    for other_bnd, other_height in other_data:
        inter = edge_line.intersection(other_bnd)
        if inter.is_empty:
            continue
        length = _get_geometry_length(inter)
        if length < MIN_SHARED_LENGTH:
            continue

        # inter can be Point, LineString, or MultiLineString
        if hasattr(inter, "geoms"):
            geoms = list(inter.geoms)
        else:
            geoms = [inter]

        for g in geoms:
            if isinstance(g, Point):
                t = _point_to_param(a, b, (g.x, g.y))
                intervals.append((t, t, other_height))
            elif hasattr(g, "coords"):
                coords = list(g.coords)
                if len(coords) >= 2:
                    t1 = _point_to_param(a, b, coords[0])
                    t2 = _point_to_param(a, b, coords[-1])
                    t_lo = min(t1, t2)
                    t_hi = max(t1, t2)
                    if t_hi - t_lo >= 1e-6:  # meaningful interval
                        intervals.append((t_lo, t_hi, other_height))

    if not intervals:
        return []

    # Merge overlapping intervals; take max height when overlapping
    intervals.sort(key=lambda x: x[0])
    merged = [list(intervals[0])]
    for t_lo, t_hi, h in intervals[1:]:
        last_lo, last_hi, last_h = merged[-1]
        if t_lo <= last_hi + 1e-6:  # overlap or adjacent
            merged[-1] = [last_lo, max(last_hi, t_hi), max(last_h, h)]
        else:
            merged.append([t_lo, t_hi, h])

    return [(m[0], m[1], m[2]) for m in merged]


def _split_param_range(
    occlusion_intervals: List[Tuple[float, float, float]],

    base_kind: FacadeSegmentKind,
) -> List[Tuple[float, float, FacadeSegmentKind, Optional[float]]]:
    """
    Split [0,1] into segments: occlusion intervals → OCCLUSION (with occlusion_height),
    remaining gaps → base_kind. Returns [(start, end, kind, occlusion_height), ...].
    """
    if not occlusion_intervals:
        return [(0.0, 1.0, base_kind, None)]

    result = []
    t = 0.0

    for occ_lo, occ_hi, occ_height in occlusion_intervals:
        if t < occ_lo - 1e-9:
            result.append((t, occ_lo, base_kind, None))
        result.append((occ_lo, occ_hi, FacadeSegmentKind.OCCLUSION, occ_height))
        t = occ_hi

    if t < 1.0 - 1e-9:
        result.append((t, 1.0, base_kind, None))

    return result


def compute_facade_definition(
    footprint_verts: List[Point2D],
    footprint_idx: int,
    all_footprints: List[List[Point2D]],
    block_vertices: Optional[List[Point2D]] = None,
    building_heights: Optional[List[float]] = None,
) -> FacadeDefinition:
    """
    Compute facade definition for a footprint from block context.

    When an edge is partially touching another building, it is split into
    segments: the touching part → OCCLUSION (with occlusion_height set to
    the occluding building's height), the free part → base kind (FRONT if
    edge touches road, else BACK). The footprint shape is unchanged.

    Args:
        footprint_verts: Vertex list of this footprint
        footprint_idx: Index of this footprint in all_footprints
        all_footprints: All footprint vertex lists (for occlusion detection)
        block_vertices: Block boundary; if None, all edges default to FRONT
        building_heights: Total height per footprint (meters). If None or
            missing for a footprint, occlusion_height is left None.

    Returns:
        FacadeDefinition with segments per edge (possibly multiple per edge
        when partially occluded). OCCLUSION segments have occlusion_height
        set to the height of the building causing the occlusion.
    """
    n = len(footprint_verts)
    if n < 3:
        from core.facade import default_facade_definition
        return default_facade_definition(max(1, n))

    block_boundary = None
    if block_vertices is not None and len(block_vertices) >= 3:
        block_poly = Polygon(block_vertices)
        if block_poly.is_valid:
            block_boundary = block_poly.boundary

    # Build other footprints' boundaries with heights (exclude self)
    other_data = []
    for i, other_verts in enumerate(all_footprints):
        if i == footprint_idx or len(other_verts) < 3:
            continue
        other_poly = Polygon(other_verts)
        if other_poly.is_valid and not other_poly.is_empty:
            h = (
                building_heights[i]
                if building_heights and i < len(building_heights)
                else 0.0
            )
            other_data.append((other_poly.boundary, float(h) if h else 0.0))

    segments = []
    for edge_idx in range(n):
        a = footprint_verts[edge_idx]
        b = footprint_verts[(edge_idx + 1) % n]

        # Base kind for non-occluded parts: FRONT if edge touches road, else BACK
        if block_boundary is not None and _edge_touches_geometry(a, b, block_boundary):
            base_kind = FacadeSegmentKind.FRONT
        else:
            base_kind = FacadeSegmentKind.BACK

        # Find parametric intervals where this edge touches other buildings
        occlusion_intervals = _get_occlusion_intervals(a, b, other_data)

        # Split edge into segments
        for start_param, end_param, kind, occ_height in _split_param_range(
            occlusion_intervals, base_kind
        ):
            if end_param - start_param < 1e-9:
                continue
            segments.append(
                FacadeSegment(
                    edge_idx=edge_idx,
                    start_param=start_param,
                    end_param=end_param,
                    kind=kind,
                    occlusion_height=occ_height if occ_height and occ_height > 0 else None,
                )
            )

    return FacadeDefinition(segments=segments)
