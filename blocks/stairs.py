"""
Block-level stairs for doors above occlusion.

When a tall building has a door on a segment above an occluded one (first
non-occlusion above occlusion), that door connects to the adjacent shorter
building. Stairs are needed to bridge the height difference. Stairs are
block elements, not building elements.

Data structure: Stair describes a ramp (45° in door direction) for mesh
generation later. No mesh geometry here - only placement and orientation.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

from shapely.geometry import LineString, Polygon

from core.footprint import Point2D
from core.facade import FacadeSegmentKind

# Minimum shared edge length to consider footprints adjacent (meters)
MIN_SHARED_LENGTH = 0.1

# Height threshold: above this, use landing + side ramp instead of simple ramp
LANDING_SIDE_RAMP_THRESHOLD = 1.0


def _get_geometry_length(geom) -> float:
    """Get total length of a geometry (LineString, MultiLineString, etc.)."""
    if geom is None or geom.is_empty:
        return 0.0
    if hasattr(geom, "length"):
        return geom.length
    if hasattr(geom, "geoms"):
        return sum(_get_geometry_length(g) for g in geom.geoms)
    return 0.0


def _find_adjacent_footprint_indices(
    footprint_verts: List[Point2D],
    footprint_idx: int,
    edge_idx: int,
    all_footprints: List[List[Point2D]],
) -> List[int]:
    """
    Find indices of footprints whose boundary touches this edge.
    Returns list of footprint indices that share at least MIN_SHARED_LENGTH with the edge.
    """
    n = len(footprint_verts)
    if n < 3 or edge_idx >= n:
        return []
    a = footprint_verts[edge_idx]
    b = footprint_verts[(edge_idx + 1) % n]
    edge_line = LineString([a, b])
    result = []
    for i, other_verts in enumerate(all_footprints):
        if i == footprint_idx or len(other_verts) < 3:
            continue
        try:
            other_poly = Polygon(other_verts)
            if not other_poly.is_valid or other_poly.is_empty:
                continue
            shared = edge_line.intersection(other_poly.boundary)
            if shared.is_empty:
                continue
            length = _get_geometry_length(shared)
            if length >= MIN_SHARED_LENGTH:
                result.append(i)
        except Exception:
            continue
    return result


@dataclass
class Stair:
    """
    A stair connecting a door (on a tall building, above occlusion) to the
    adjacent shorter building's roof.

    Data structure only - mesh generation uses this as input.

    Two variants:
    - ramp: Simple 45° ramp in door direction (when drop <= threshold).
    - landing_side_ramp: Horizontal square landing in front of door, then side
      ramp going down. Side ramp direction = along facade, toward more space.
    """

    from_building_idx: int
    """Index of the building with the door."""

    from_floor_idx: int
    """Floor index where the door is."""

    from_position: Point2D
    """(x, y) of the door center."""

    from_z: float
    """Z height at door (floor base)."""

    to_building_idx: int
    """Index of the adjacent (shorter) building - landing is its roof."""

    to_z: float
    """Z height of the landing (top of shorter building)."""

    direction: Tuple[float, float]
    """Outward direction from door (normalized)."""

    ramp_angle: float = 45.0
    """Ramp slope in degrees (45° = 1:1). For mesh generation."""

    variant: str = "ramp"
    """'ramp' = simple ramp; 'landing_side_ramp' = landing + side ramp."""

    side_ramp_direction: Optional[Tuple[float, float]] = None
    """Direction along facade for side ramp (when variant is landing_side_ramp)."""


def collect_stairs_from_buildings(
    buildings: List,
    footprints: List[List[Point2D]],
    facade_definitions: List,
    building_heights: List[float],
    building_params_list: Optional[List[dict]] = None,
    **default_generation_params
) -> List[Stair]:
    """
    Collect stairs for doors that are above occlusion (connecting to adjacent building).

    For each door on floor > 0 that lies on a segment which was OCCLUSION on the
    floor below, find the adjacent (shorter) building and create a Stair.

    Args:
        buildings: List of Building objects (with floors, doors)
        footprints: Footprint vertex lists (for adjacency lookup)
        facade_definitions: FacadeDefinition per building
        building_heights: Total height per building (meters)
        building_params_list: Per-building generation params (merged with defaults)
        **default_generation_params: Default params for floor.get_doors()

    Returns:
        List of Stair objects
    """
    stairs = []
    for bldg_idx, building in enumerate(buildings):
        if building is None or bldg_idx >= len(footprints) or bldg_idx >= len(facade_definitions):
            continue
        footprint = footprints[bldg_idx]
        facade = facade_definitions[bldg_idx]
        my_height = building_heights[bldg_idx] if bldg_idx < len(building_heights) else 0.0
        cumul = building._cumulative_heights

        gen_params = dict(default_generation_params)
        if building_params_list and bldg_idx < len(building_params_list) and building_params_list[bldg_idx]:
            gen_params.update(building_params_list[bldg_idx])
        gen_params.pop("floor_height", None)  # Not needed for doors
        gen_params.setdefault("cumulative_heights", cumul)

        for floor_idx in range(1, building.num_floors):
            floor = building.get_floor(floor_idx)
            z_base = cumul[floor_idx]
            z_top = cumul[floor_idx + 1] if floor_idx + 1 < len(cumul) else z_base + floor.height
            prev_z_base = cumul[floor_idx - 1]
            prev_z_top = cumul[floor_idx]

            doors = floor.get_doors(seed=building.seed, **gen_params)

            for door in doors:
                edge_idx = door.edge_idx
                param = door.position_on_edge
                seg = facade.get_segment_at(edge_idx, param, z_base, z_top)
                if seg is None:
                    continue
                # Check if this segment was OCCLUSION on the floor below
                prev_eff = seg.effective_kind_at_height(prev_z_base, prev_z_top)
                if prev_eff != FacadeSegmentKind.OCCLUSION:
                    continue

                # Find adjacent footprint (shorter building we connect to)
                adj_indices = _find_adjacent_footprint_indices(
                    footprint, bldg_idx, edge_idx, footprints
                )
                if not adj_indices:
                    continue
                # Pick the adjacent with highest roof that is still below us (the landing)
                best_adj = None
                best_landing_z = -1.0
                for adj_idx in adj_indices:
                    adj_h = building_heights[adj_idx] if adj_idx < len(building_heights) else 0.0
                    if adj_h >= my_height:
                        continue
                    if adj_h > best_landing_z:
                        best_landing_z = adj_h
                        best_adj = adj_idx
                if best_adj is None:
                    continue

                pos = door.get_world_position()
                from_z = z_base  # Start at floor level (bottom of door)
                drop = from_z - best_landing_z
                if drop <= 0:
                    continue  # No height difference, no stair needed

                # Variant: simple ramp vs landing + side ramp
                variant = "ramp"
                side_ramp_direction = None
                if drop > LANDING_SIDE_RAMP_THRESHOLD:
                    variant = "landing_side_ramp"
                    # Edge direction (along facade)
                    es, ee = door.edge_start, door.edge_end
                    ex = ee[0] - es[0]
                    ey = ee[1] - es[1]
                    edge_len = math.sqrt(ex * ex + ey * ey) or 1e-9
                    edge_dir = (ex / edge_len, ey / edge_len)
                    # Space toward start vs end of segment
                    space_toward_start = (param - seg.start_param) * edge_len
                    space_toward_end = (seg.end_param - param) * edge_len
                    # Ramp goes toward more space
                    if space_toward_end >= space_toward_start:
                        side_ramp_direction = edge_dir
                    else:
                        side_ramp_direction = (-edge_dir[0], -edge_dir[1])

                stair = Stair(
                    from_building_idx=bldg_idx,
                    from_floor_idx=floor_idx,
                    from_position=pos,
                    from_z=from_z,
                    to_building_idx=best_adj,
                    to_z=best_landing_z,
                    direction=door.facing_direction,
                    ramp_angle=45.0,
                    variant=variant,
                    side_ramp_direction=side_ramp_direction,
                )
                stairs.append(stair)

    return stairs
