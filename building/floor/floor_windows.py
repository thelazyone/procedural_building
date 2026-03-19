"""
Window placement logic for floors.

Facade-aware: windows only on FRONT and BACK segments (none on OCCLUSION).
Merged segments: collinear same-kind treated as one for distribution.
Front has higher density than back. Uses fixed slot grid for alignment across floors.
"""

import math
import random
from typing import List, Tuple, Optional
from .floor import Floor
from .facade_segments import get_merged_segments_for_windows
from building.window import Window, WindowGenerator
from core.facade import FacadeSegmentKind

# Defaults when not in params (from building param generator averages)
DEFAULT_FRONT_DENSITY_MULT = 1.8
DEFAULT_BACK_DENSITY_MULT = 1.2
DEFAULT_WINDOW_FILL_PROB = 0.3  # Lower so many slots stay empty


def _get_edge_length(edges: List, edge_idx: int) -> float:
    """Get length of edge in meters."""
    start, end = edges[edge_idx]
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    return math.sqrt(dx * dx + dy * dy)


def _get_slot_params_for_segment(
    edge_length: float,
    edge_spacing: float,
    window_spacing: float,
    start_param: float,
    end_param: float,
    density_mult: float,
) -> List[float]:
    """
    Slot positions (param 0..1) for a segment. Density multiplier modifies effective spacing:
    higher mult = tighter spacing = more windows. effective_spacing = window_spacing / mult.
    """
    # Clamp to edge_spacing from edge ends
    margin = edge_spacing / edge_length
    start_param = max(start_param, margin)
    end_param = min(end_param, 1.0 - margin)
    if end_param <= start_param:
        return []

    seg_length_m = edge_length * (end_param - start_param)
    if seg_length_m < 0.5:
        return []
    # Effective spacing: divide by density_mult so front (higher mult) gets tighter slots
    effective_spacing = window_spacing / density_mult
    n = max(1, int(seg_length_m / effective_spacing))
    seg_usable = end_param - start_param
    return [start_param + seg_usable * i / (n + 1) for i in range(1, n + 1)]


def generate_windows(
    floor: Floor,
    seed: int,
    door_occupied_segments: Optional[List[List[Tuple[float, float]]]] = None,
    window_density: float = 0.3,
    edge_spacing: float = 1.0,
    window_spacing: float = 1.5,
    cumulative_heights: Optional[List[float]] = None,
    **params
) -> List[Window]:
    """
    Generate windows for a floor. Facade-aware: FRONT (higher density), BACK (lower),
    none on OCCLUSION. Merges collinear same-kind segments. Uses slot grid for alignment.
    door_occupied_segments: used only for REMOVAL after doors placed (pass empty initially).
    """
    footprint = floor.footprint
    edges = footprint.get_edges()
    facade = floor.get_facade_definition()

    # Floor Z range for effective kind
    if cumulative_heights and floor.floor_idx < len(cumulative_heights):
        z_base = cumulative_heights[floor.floor_idx]
        z_top = cumulative_heights[floor.floor_idx + 1] if floor.floor_idx + 1 < len(cumulative_heights) else z_base + floor.height
    else:
        z_base = floor.floor_idx * floor.height
        z_top = z_base + floor.height

    merged = get_merged_segments_for_windows(facade, z_base, z_top)
    edge_lengths = [_get_edge_length(edges, i) for i in range(len(edges))]
    window_generator = WindowGenerator()
    windows = []
    placed_on_edge = {}  # edge_idx -> [(param, effective_spacing), ...]

    front_mult = params.get("front_window_density_mult", DEFAULT_FRONT_DENSITY_MULT)
    back_mult = params.get("back_window_density_mult", DEFAULT_BACK_DENSITY_MULT)
    fill_prob = params.get("window_fill_prob", DEFAULT_WINDOW_FILL_PROB)

    for mseg in merged:
        edge_idx = mseg.edge_idx
        edge_len = edge_lengths[edge_idx]
        edge_start, edge_end = edges[edge_idx]
        mult = front_mult if mseg.kind == FacadeSegmentKind.FRONT else back_mult
        effective_spacing = window_spacing / mult

        slots = _get_slot_params_for_segment(
            edge_len, edge_spacing, window_spacing,
            mseg.start_param, mseg.end_param, mult,
        )
        if edge_idx not in placed_on_edge:
            placed_on_edge[edge_idx] = []

        for slot_idx, param in enumerate(slots):
            abs_pos = param * edge_len
            # Enforce spacing: no overlap with already-placed windows on this edge
            conflict = any(
                abs(abs_pos - p * edge_len) < max(eff_sp, effective_spacing)
                for p, eff_sp in placed_on_edge[edge_idx]
            )
            if conflict:
                continue

            slot_seed = hash((seed, "win_slot", edge_idx, round(param, 4))) % (2**31)
            if random.Random(slot_seed).random() > fill_prob:
                continue

            # Check door occupancy (for removal pass - if doors already placed)
            if door_occupied_segments and edge_idx < len(door_occupied_segments):
                collision = False
                for occ_start, occ_end in door_occupied_segments[edge_idx]:
                    if not (abs_pos + window_spacing / 2 < occ_start or abs_pos - window_spacing / 2 > occ_end):
                        collision = True
                        break
                if collision:
                    continue

            # Facing direction
            dx = edge_end[0] - edge_start[0]
            dy = edge_end[1] - edge_start[1]
            length = math.sqrt(dx * dx + dy * dy)
            if length < 1e-9:
                continue
            normal_x = dy / length
            normal_y = -dx / length
            if not footprint.is_ccw:
                normal_x, normal_y = -normal_x, -normal_y

            window_seed = hash((seed, "window", edge_idx, slot_idx, floor.floor_idx)) % (2**31)
            window_props = window_generator.generate(
                parent_context=floor,
                seed=window_seed,
                window_idx=len(windows),
                total_windows=len(slots),
                floor_idx=floor.floor_idx,
                **params
            )

            windows.append(Window(
                edge_idx=edge_idx,
                position_on_edge=param,
                edge_start=edge_start,
                edge_end=edge_end,
                facing_direction=(normal_x, normal_y),
                floor_idx=floor.floor_idx,
                properties=window_props,
            ))
            placed_on_edge[edge_idx].append((param, effective_spacing))

    return windows
