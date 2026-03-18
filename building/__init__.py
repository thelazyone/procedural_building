"""Building generation (Layer 4).

Footprint → Building → Floors → Doors, Windows, Corners.
"""

from .building import Building
from .params_generator import generate_building_params
from .floor import FloorGenerator
from .floor.floor import Floor
from .door import Door, DoorGenerator, DoorProperties
from .window import Window, WindowGenerator, WindowProperties
from .corner import Corner, CornerGenerator, CornerProperties

__all__ = [
    'Building', 'Floor', 'FloorGenerator', 'generate_building_params',
    'Door', 'Window', 'Corner',
    'DoorGenerator', 'DoorProperties',
    'WindowGenerator', 'WindowProperties',
    'CornerGenerator', 'CornerProperties',
]
