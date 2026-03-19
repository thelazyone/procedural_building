"""
Procedural Building Generator

A hierarchical, deterministic system for generating building structures.
"""

__version__ = "0.1.0"

from .core.footprint import Footprint
from .core.facade import (
    FacadeSegmentKind,
    FacadeSegment,
    FacadeDefinition,
    default_facade_definition,
    build_facade_from_edge_segments,
)
from .building import Building
from .building.floor.floor import Floor

__all__ = [
    "Building",
    "Footprint",
    "Floor",
    "FacadeSegmentKind",
    "FacadeSegment",
    "FacadeDefinition",
    "default_facade_definition",
    "build_facade_from_edge_segments",
]
