"""
Door placement logic for floors.

Facade-aware: doors only on FRONT and BACK segments (none on OCCLUSION).
No merging of segments. Ground floor: normal door logic. Higher floors: doors
only on above_occlusion segments (first non-occlusion above occlusion) with a chance.
Doors ignore window positions when placing.
"""

import math
import random
from typing import List, Tuple, Optional
from .floor import Floor
from .facade_segments import get_unmerged_segments_for_doors
from building.door import Door, DoorGenerator
from core.footprint import Point2D


def _get_edge_length(edges: List, edge_idx: int) -> float:
    """Get length of edge in meters."""
    start, end = edges[edge_idx]
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    return math.sqrt(dx * dx + dy * dy)


def _find_closest_valid_position(
    target_pos: float,
    edge_length: float,
    occupied_segments: List[Tuple[float, float]],
    edge_spacing: float,
    door_spacing: float,
) -> Optional[float]:
    """Find closest valid position that doesn't collide."""
    step = 0.1
    best_position = None
    best_distance = float('inf')
    for offset in range(int(door_spacing / step) + 1):
        for direction in [1, -1]:
            if offset == 0 and direction == -1:
                continue
            test_pos = target_pos + direction * offset * step
            if test_pos < edge_spacing or test_pos > edge_length - edge_spacing:
                continue
            valid = True
            for occ_start, occ_end in occupied_segments:
                if not (test_pos + door_spacing / 2 < occ_start or test_pos - door_spacing / 2 > occ_end):
                    valid = False
                    break
            if valid and abs(test_pos - target_pos) < best_distance:
                best_distance = abs(test_pos - target_pos)
                best_position = test_pos
    return best_position


def _weighted_random_choice(rng: random.Random, items: List, weights: List[float]) -> int:
    """Choose index weighted by values."""
    total = sum(weights)
    r = rng.uniform(0, total)
    cumulative = 0.0
    for i, w in enumerate(weights):
        cumulative += w
        if r <= cumulative:
            return i
    return len(items) - 1


def generate_doors(
    floor: Floor,
    seed: int,
    door_density: float = 0.05,
    edge_spacing: float = 1.0,
    door_spacing: float = 2.0,
    above_occlusion_door_chance: float = 0.3,
    cumulative_heights: Optional[List[float]] = None,
    **params
) -> Tuple[List[Door], List[List[Tuple[float, float]]]]:
    """
    Generate doors for a floor. Facade-aware: only on FRONT/BACK segments.
    Ground floor: normal density. Higher floors: only on above_occlusion segments (chance).
    Doors ignore windows when placing. Returns (doors, occupied_segments for window removal).
    """
    rng = random.Random(seed)
    footprint = floor.footprint
    edges = footprint.get_edges()
    facade = floor.get_facade_definition()

    if cumulative_heights and floor.floor_idx < len(cumulative_heights):
        z_base = cumulative_heights[floor.floor_idx]
        z_top = cumulative_heights[floor.floor_idx + 1] if floor.floor_idx + 1 < len(cumulative_heights) else z_base + floor.height
        prev_z_base = cumulative_heights[floor.floor_idx - 1] if floor.floor_idx > 0 else None
        prev_z_top = cumulative_heights[floor.floor_idx] if floor.floor_idx > 0 else None
    else:
        z_base = floor.floor_idx * floor.height
        z_top = z_base + floor.height
        prev_z_base = (floor.floor_idx - 1) * floor.height if floor.floor_idx > 0 else None
        prev_z_top = floor.floor_idx * floor.height if floor.floor_idx > 0 else None

    unmerged = get_unmerged_segments_for_doors(
        facade, z_base, z_top, floor.floor_idx, prev_z_base, prev_z_top
    )
    if not unmerged:
        return [], [[] for _ in range(len(edges))]

    occupied_segments = [[] for _ in range(len(edges))]
    doors = []
    door_generator = DoorGenerator()
    edge_lengths = [_get_edge_length(edges, i) for i in range(len(edges))]

    # Determine door candidates
    if floor.floor_idx == 0:
        candidates = [(m, 1.0) for m in unmerged]
        seg_lengths = [edge_lengths[m.edge_idx] * (m.end_param - m.start_param) for m in unmerged]
        num_doors = max(1, int(sum(seg_lengths) * door_density)) if seg_lengths else 1
    else:
        candidates = [
            (m, 1.0) for m in unmerged
            if m.above_occlusion and rng.random() < above_occlusion_door_chance
        ]
        if not candidates:
            return [], occupied_segments
        seg_lengths = [1.0] * len(candidates)
        num_doors = len(candidates)

    for door_idx in range(num_doors):
        placed = False
        for _ in range(10):
            idx = _weighted_random_choice(rng, candidates, seg_lengths)
            m, _ = candidates[idx]

            edge_idx = m.edge_idx
            edge_start, edge_end = edges[edge_idx]
            edge_length = edge_lengths[edge_idx]
            seg_len_param = m.end_param - m.start_param
            if seg_len_param < 0.02:
                continue

            target_param = m.start_param + seg_len_param * rng.uniform(0.2, 0.8)
            abs_position = target_param * edge_length

            collision = any(
                not (abs_position + door_spacing / 2 < os or abs_position - door_spacing / 2 > oe)
                for os, oe in occupied_segments[edge_idx]
            )
            if collision:
                abs_position = _find_closest_valid_position(
                    abs_position, edge_length, occupied_segments[edge_idx],
                    edge_spacing, door_spacing
                )
                if abs_position is None:
                    continue
                target_param = abs_position / edge_length

            placed = True
            occupied_segments[edge_idx].append((
                abs_position - door_spacing / 2,
                abs_position + door_spacing / 2,
            ))

            dx = edge_end[0] - edge_start[0]
            dy = edge_end[1] - edge_start[1]
            length = math.sqrt(dx * dx + dy * dy)
            if length < 1e-9:
                placed = False
                continue
            normal_x = dy / length
            normal_y = -dx / length
            if not footprint.is_ccw:
                normal_x, normal_y = -normal_x, -normal_y

            door_seed = hash((seed, "door", door_idx, floor.floor_idx)) % (2**31)
            door_props = door_generator.generate(
                parent_context=floor,
                seed=door_seed,
                door_idx=door_idx,
                total_doors=num_doors,
                **params
            )

            doors.append(Door(
                edge_idx=edge_idx,
                position_on_edge=target_param,
                edge_start=edge_start,
                edge_end=edge_end,
                facing_direction=(normal_x, normal_y),
                floor_idx=floor.floor_idx,
                properties=door_props,
            ))
            break

    return doors, occupied_segments
