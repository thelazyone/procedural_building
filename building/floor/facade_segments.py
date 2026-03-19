"""
Facade segment helpers for window and door placement.

- Merged segments: collinear same-kind segments merged (for window placement)
- Unmerged segments: each segment separate (for door placement)
- Above-occlusion: segment that is first non-occlusion above an occlusion segment
"""

from typing import List, Tuple
from dataclasses import dataclass

from core.facade import FacadeDefinition, FacadeSegmentKind


@dataclass
class MergedSegment:
    """A merged span (edge_idx, start_param, end_param, kind) for window placement."""
    edge_idx: int
    start_param: float
    end_param: float
    kind: FacadeSegmentKind


@dataclass
class UnmergedSegment:
    """A single segment (no merging) for door placement. Includes above_occlusion flag."""
    edge_idx: int
    start_param: float
    end_param: float
    kind: FacadeSegmentKind
    above_occlusion: bool


def get_merged_segments_for_windows(
    facade: FacadeDefinition,
    floor_z_base: float,
    floor_z_top: float,
) -> List[MergedSegment]:
    """
    Get segments for window placement: merge adjacent same-kind segments on each edge.
    Excludes OCCLUSION (no windows there).
    """
    # Group by edge, get effective kind per segment
    edge_segments = {}
    for seg in facade.segments:
        eff = seg.effective_kind_at_height(floor_z_base, floor_z_top)
        if eff == FacadeSegmentKind.OCCLUSION:
            continue
        ei = seg.edge_idx
        if ei not in edge_segments:
            edge_segments[ei] = []
        edge_segments[ei].append((seg.start_param, seg.end_param, eff))

    merged = []
    for edge_idx in sorted(edge_segments.keys()):
        segs = sorted(edge_segments[edge_idx], key=lambda x: x[0])
        # Merge adjacent same-kind
        i = 0
        while i < len(segs):
            start, end, kind = segs[i]
            j = i + 1
            while j < len(segs) and segs[j][2] == kind and segs[j][0] <= end + 1e-9:
                end = max(end, segs[j][1])
                j += 1
            merged.append(MergedSegment(edge_idx=edge_idx, start_param=start, end_param=end, kind=kind))
            i = j

    return merged


def get_unmerged_segments_for_doors(
    facade: FacadeDefinition,
    floor_z_base: float,
    floor_z_top: float,
    floor_idx: int,
    prev_floor_z_base: float,
    prev_floor_z_top: float,
) -> List[UnmergedSegment]:
    """
    Get segments for door placement: no merging. Each segment considered separately.
    Excludes OCCLUSION. Marks above_occlusion=True when this segment was OCCLUSION
    on the floor below (first non-occlusion above occlusion).
    """
    result = []
    for seg in facade.segments:
        eff = seg.effective_kind_at_height(floor_z_base, floor_z_top)
        if eff == FacadeSegmentKind.OCCLUSION:
            continue
        above_occlusion = False
        if floor_idx > 0 and prev_floor_z_base is not None:
            prev_eff = seg.effective_kind_at_height(prev_floor_z_base, prev_floor_z_top)
            if prev_eff == FacadeSegmentKind.OCCLUSION:
                above_occlusion = True
        result.append(UnmergedSegment(
            edge_idx=seg.edge_idx,
            start_param=seg.start_param,
            end_param=seg.end_param,
            kind=eff,
            above_occlusion=above_occlusion,
        ))
    return result
