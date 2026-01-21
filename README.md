# Procedural Building Generator

A Python library for a deterministic procedural building generator.
The deterministic aspect allows for **Lazy Generation** of content, which is optimal for game environments or LOD changes. Buildings are defined with footprints, divided in rooms, in a similar way to the Project Zomboid editor.
Various data structures are **hierarchically** linked to allow modular approach to development and different use cases.
The generator adopts a topological approach (basically, graph based) and the 3D meshes appear later. In fact, they could not be used at all, and this could work for a pixel art sprite-based game just as well.

The project is barely a draft of an idea, waaaays in **early development**.

## Structure

- `core/`: Foundation classes (footprint, building, generator base)
- `generators/`: Hierarchical element generators
- `utils/`: Seeding, coordinate conversion utilities
- `docs/`: Architecture documentation
- `debug_viewer/`: Standalone 3D visualization tool

## Quick Start

```python
from procedural_building.core.building import Building

# Define floor footprint (one per floor)
floor_footprint = [
    [(0, 0), (10, 0), (10, 8), (0, 8)],  # Floor 1
    [(0, 0), (10, 0), (10, 8), (0, 8)]   # Floor 2
]

# Create building with seed
building = Building(floor_footprint, seed=12345, floor_height=3.0)

# Lazy generation - triggers on access
walls = building.get_walls()
for wall in walls:
    windows = wall.get_windows(density=0.3)
```

## Requirements

- Python 3.8+
- Shapely (for polygon operations)

## Documentation

See `docs/ARCHITECTURE.md` for design principles and patterns.

## License

MIT License - See LICENSE file
