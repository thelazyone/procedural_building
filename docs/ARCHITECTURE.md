# Procedural Building - Architecture
Expanding from what is in the README.md:

## Module Structure

### `core/`
Foundation classes used throughout:
- `footprint.py`: Wrapper around Shapely for non-convex polygon operations
- `building.py`: Building data structure (floors as footprint + parameters)
- `generator_base.py`: Base class defining generator interface

### `generators/`
Hierarchical generators, each following the pattern:
```python
def generate(parent_context, seed, **params) -> result
```
- `building_exterior.py`: Generates exterior structure from floor footprint
- `wall.py`: Generates wall segments from polygon edges
- `corner.py`: Generates corner details at polygon vertices
- `window.py`: Generates windows along wall segments
- `door.py`: Generates doors/entrances

### `utils/`
- `seeding.py`: Deterministic seed derivation for sub-generators
- `coordinates.py`: Coordinate system conversion (Z-up ↔ Y-up)

### `debug_viewer/`
Standalone Python app (separate from library):
- Left panel: Parameters + visibility toggles
- Right panel: 3D view (rotation, pan)
- Live regeneration on parameter change

## Key Patterns

### Generator Signature
All generators follow this interface:
```python
def generate(parent_context, seed, **params):
    """
    Args:
        parent_context: Data from parent (e.g., wall segment for window gen)
        seed: int for deterministic RNG
        **params: Style/density/constraint parameters
    
    Returns:
        Generated elements (cached after first call)
    """
```

### Lazy Access
```python
# No computation happens until query:
building = Building(floor_footprint, seed=12345)

# Generation triggered here:
walls = building.get_walls()

# Generation triggered per wall:
for wall in walls:
    windows = wall.get_windows(density=0.3)
```

### Seed Propagation
Each generator derives child seeds deterministically:
```python
wall_seed = hash((building_seed, wall_id)) % MAX_SEED
```

## Units & Coordinates

- **Units**: Meters (typical for game/architectural scale)
- **Coordinate System**: Z-up by default
- **Conversion**: `coordinates.py` handles Y-up output when needed (e.g., for specific engines)

## Future Scope (Not Now)

- Interiors (rooms, room layouts)
- Roofs
- Curved/organic shapes
- Serialization/save formats
- Multi-building city generation
- 3D mesh/asset generation
