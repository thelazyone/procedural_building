# Placement Algorithm

## Overview

The FloorGenerator uses a sophisticated collision-aware placement algorithm for doors (and future windows) that ensures proper spacing and distribution.

## Key Features

### 1. Collision Tracking
- Maintains a map of occupied segments on each edge
- Each placed object reserves a segment: `[position - spacing/2, position + spacing/2]`
- New objects cannot overlap with occupied segments

### 2. Placement Strategy

For each object to place:

1. **Random Edge Selection** (weighted by edge length)
2. **Random Position** along that edge
3. **Collision Check**:
   - If position is free → place object there
   - If position collides → find closest valid position
   - If no valid position found after multiple attempts → skip object

### 3. Closest Valid Position Search

When initial position collides:
1. Search outward from target position in 0.1m steps
2. Check both directions (left and right)
3. Find the closest position that:
   - Doesn't collide with any occupied segment
   - Respects edge_spacing from corners
   - Respects door_spacing from other doors
4. If found → place object at that position
5. If not found → try different edge (up to 10 attempts per object)

## Parameters

### door_spacing (hidden, default: 2.0m)
Minimum distance between door centers.

**Example:**
- 40m perimeter building
- door_spacing = 2.0m
- Maximum possible doors ≈ 40 / 2 = 20 doors

### edge_spacing (default: 1.0m)
Minimum distance from edge corners.

Prevents doors from being placed too close to building corners.

## Results

### Test: 40m Perimeter Square Building

**Density 0.025 (1 door):**
- 1 door placed successfully

**Density 0.05 (2 doors):**
- 2 doors placed on different edges

**Density 0.1 (4 doors):**
- 4 doors distributed across multiple edges
- Doors on same edge respect 2m spacing

**Density 0.2 (8 doors):**
```
Edge 0: 1 door at -0.54m
Edge 1: 2 doors at -3.92m and -1.85m (2.07m apart)
Edge 2: 2 doors at 2.71m and 0.71m (2.00m apart)
Edge 3: 3 doors at 1.61m, 3.67m, -0.40m (all ~2m apart)
```

## Future Extensions

### Window Placement
The same algorithm will be used for windows with different spacing:
- `window_spacing` ≈ 0.5m (windows can be closer together)
- Check collision with both doors AND windows

### Collision Map Structure
```python
edge_objects = [
    {
        'edge_idx': 0,
        'objects': [
            {'type': 'door', 'position': 5.2, 'spacing': 2.0},
            {'type': 'window', 'position': 8.5, 'spacing': 0.5},
        ]
    },
    ...
]
```

This allows windows to be placed in gaps between doors, respecting both door and window spacing requirements.

## Advantages

1. **No Infinite Loops**: Uses attempt limits instead of while-true loops
2. **Graceful Degradation**: Skips objects that can't be placed
3. **Linear Performance**: O(n × m) where n = doors, m = attempts per door
4. **Predictable**: Deterministic based on seed
5. **Extensible**: Same algorithm works for doors, windows, decorations, etc.

## Trade-offs

- May place fewer objects than requested if building is small/crowded
- "Closest valid position" may not be uniform distribution
- Earlier placements get priority (main entrance gets best position)

These trade-offs are acceptable for procedural generation where visual quality > perfect uniformity.
