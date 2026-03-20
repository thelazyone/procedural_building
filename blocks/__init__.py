"""
Block extraction and subdivision (Layer 2).

Graph → polygons (blocks) → shrink (setback) → divide (longest-edge).
"""

from .subdivide import subdivide_block
from .merge_fragments import merge_footprints_to_min_area
from .filter_internal import filter_footprints_touching_block
from .gap import apply_gaps
from .facade_noise import apply_facade_noise
from .stairs import Stair, collect_stairs_from_buildings

__all__ = [
    'subdivide_block',
    'merge_footprints_to_min_area',
    'filter_footprints_touching_block',
    'apply_gaps',
    'apply_facade_noise',
    'Stair',
    'collect_stairs_from_buildings',
]
