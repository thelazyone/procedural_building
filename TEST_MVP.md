# MVP Testing Guide

## What Was Implemented

### 1. Core Data Structures ✅
- **Footprint**: Shapely-based polygon wrapper for floor outlines
  - Supports non-convex shapes
  - Validates geometry
  - Provides vertices, edges, area, perimeter
  
- **Floor**: Container for footprint + height + floor index
  - Individual height per floor
  - Z-positioning helpers
  
- **Building**: Multi-floor structure
  - Accepts Floor objects or raw vertex lists
  - Per-floor height support
  - Cumulative height tracking

### 2. Debug Viewer ✅
- **3D Visualization**: pygame + PyOpenGL
  - Orbit camera (mouse drag to rotate, scroll to zoom)
  - Grid floor
  - Footprint rendering at correct Z heights
  
- **UI Panel**: pygame_gui
  - Building type dropdown
  - Load/Clear buttons
  - Seed parameter input
  - Visibility toggles (footprints active, others disabled for future)

### 3. Building Templates ✅
- **Simple House**: 10x10m, 3 stories, uniform 3m floor heights

## Testing Steps

### Step 1: Install Dependencies

```bash
# From project root
pip install -e .

# Install viewer dependencies  
pip install pygame PyOpenGL PyOpenGL-accelerate pygame-gui
```

### Step 2: Test Core Library

Run the example script to verify the API:

```bash
python examples/simple_building.py
```

**Expected output:**
- Building created with 3 floors
- Total height: 9.0m
- Each floor: 100m² area, 40m perimeter
- L-shaped building: 75m² area

### Step 3: Launch Debug Viewer

```bash
python -m debug_viewer
```

**Expected behavior:**
1. Window opens (1400x900)
2. Left panel shows UI controls
3. Right side shows 3D view with grid
4. "Simple House" is pre-selected in dropdown

### Step 4: Load Building

1. Click **"Load"** button
2. Console should print:
   ```
   Loaded Simple House with seed 12345
     Floors: 3
     Total height: 9.0m
   ```
3. Three blue squares appear in 3D view at Z=0, Z=3, Z=6

### Step 5: Test Camera

- **Rotate**: Left-click drag to orbit around building
- **Zoom**: Scroll wheel to zoom in/out
- Building should stay centered, camera orbits around (5, 5, 4.5)

### Step 6: Test Visibility Toggle

1. Click **"☑ Show Footprints"** checkbox
2. Footprints disappear
3. Click again to show them

### Step 7: Test Clear

1. Click **"Clear"** button
2. Console prints: "Building cleared"
3. Footprints disappear from view

### Step 8: Test Seed

1. Change seed value to something else (e.g., 99999)
2. Click **"Load"**
3. Building loads (no visual difference yet since generation is deterministic but simple)

## Troubleshooting

### "No module named 'shapely'"
```bash
pip install shapely
```

### "No module named 'pygame_gui'"
```bash
pip install pygame-gui
```

### OpenGL errors
Try:
```bash
pip install PyOpenGL PyOpenGL-accelerate --upgrade
```

### Import errors with procedural_building
Make sure you installed in development mode:
```bash
pip install -e .
```

## What to See

When working correctly, you should see:
- Dark gray background
- Light gray grid on ground plane (Z=0)
- Three semi-transparent blue squares (footprints) stacked vertically:
  - Ground floor at Z=0
  - Second floor at Z=3m
  - Third floor at Z=6m
- Darker blue outlines around each footprint
- Smooth camera rotation when dragging
- Responsive zoom

## Next Steps

Once MVP is verified, you can:
1. Add more building templates (L-shaped, T-shaped, etc.)
2. Implement wall generation
3. Add window placement
4. Implement door generation
5. Add corner details

The architecture is ready for hierarchical generation!
