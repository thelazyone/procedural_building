"""
Block extraction and subdivision (Layer 2).

Graph → polygons (blocks) → shrink (setback) → divide (longest-edge).
"""

from .subdivide import subdivide_block
from .filter_internal import filter_footprints_touching_block
from .split_concave import split_concave_footprints
from .gap import apply_gaps
from .facade_noise import apply_facade_noise
from .stairs import Stair, collect_stairs_from_buildings

__all__ = [
    'subdivide_block',
    'filter_footprints_touching_block',
    'split_concave_footprints',
    'apply_gaps',
    'apply_facade_noise',
    'Stair',
    'collect_stairs_from_buildings',
]
