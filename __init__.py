"""
Procedural Building Generator

A hierarchical, deterministic system for generating building structures.
"""

__version__ = "0.1.0"

from .core.footprint import Footprint
from .building import Building
from .building.floor.floor import Floor

__all__ = ["Building", "Footprint", "Floor"]
