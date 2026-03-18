# Procedural Building - Architecture
Expanding from what is in the README.md:

## Module Structure

The project is organized into five component layers (street network → blocks → parcels → building → interior):

### `street_network/` (Layer 1)
Tensor field → road graph → graph refinement (close open ends).
Future: tensor_field, road_graph, graph_refinement.

### `blocks/` (Layer 2)
Graph → polygons (blocks) → shrink (setback) → divide (longest-edge).
Future: block_extraction, block_shrink, block_divide.

### `parcels/` (Layer 3)
Parcel subdivision, footprint generation, road-access filter.
Future: subdivision, footprint_generator, road_access_filter.

### `building/` (Layer 4)
Footprint → Building → Floors → Doors, Windows, Corners.
- `building/`: Building data structure
- `floor/`: FloorGenerator, floor_doors, floor_windows, floor_corners
- `door.py`, `window.py`, `corner.py`, `wall.py`: Element generators

### `interior/` (Layer 5)
Rooms, corridors, furniture inside buildings.
Future: room_layout, corridor, furniture.

### `core/`
Foundation classes used throughout:
- `footprint.py`: Wrapper around Shapely for non-convex polygon operations
- `generator_base.py`: Base class defining generator interface
- `camera.py`: Orbit camera for 3D viewers
- `simple_ui.py`: UI components (Button, Label, TextInput, Checkbox, RadioButton) for viewers

### `utils/`
- `seeding.py`: Deterministic seed derivation for sub-generators
- `coordinates.py`: Coordinate system conversion (Z-up ↔ Y-up)

### `building_viewer/`
Standalone Python app (separate from library):
- Left panel: Parameters + visibility toggles
- Right panel: 3D view (rotation, pan)
- Live regeneration on parameter change

## Key Patterns

### Generator Signature
All generators (in `building/` and future layers) follow this interface:
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

- Street network (tensor field, road graph) — `street_network/`
- Blocks (extraction, shrink, divide) — `blocks/`
- Parcels (subdivision, road-access) — `parcels/`
- Interiors (rooms, room layouts) — `interior/`
- Roofs
- Curved/organic shapes
- Serialization/save formats
- 3D mesh/asset generation
