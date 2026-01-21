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

### Installation

```bash
# Install core library
pip install -e .

# Install debug viewer dependencies
cd debug_viewer
pip install -r requirements.txt
```

See [SETUP.md](SETUP.md) for detailed installation instructions.

### Running the Debug Viewer

```bash
python -m debug_viewer
```

**Controls:**
- Left mouse drag: Rotate camera
- Mouse wheel: Zoom
- Load button: Load selected building
- Clear button: Remove building

### Using the Library

```python
from procedural_building import Building

# Define floor footprints (one per floor)
floor_footprints = [
    [(0, 0), (10, 0), (10, 10), (0, 10)],  # Floor 1
    [(0, 0), (10, 0), (10, 10), (0, 10)],  # Floor 2
    [(0, 0), (10, 0), (10, 10), (0, 10)],  # Floor 3
]

# Create building with seed
building = Building(
    floors=floor_footprints,
    seed=12345,
    floor_heights=[3.0, 3.0, 3.0]
)

# Access building data (lazy evaluation)
print(f"Floors: {building.num_floors}")
print(f"Total height: {building.get_total_height():.1f}m")

# Inspect individual floors
for i in range(building.num_floors):
    floor = building.get_floor(i)
    print(f"Floor {i}: {floor.footprint.area():.1f}m²")
```

## Documentation

- [SETUP.md](SETUP.md) - Installation and setup guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Design principles and patterns
- [examples/](examples/) - Code examples

## Requirements

- Python 3.8+
- Shapely >= 2.0.0 (polygon operations)
- pygame >= 2.5.0 (for debug viewer)
- PyOpenGL >= 3.1.6 (for debug viewer)

## License

MIT License - See [LICENSE](LICENSE)
