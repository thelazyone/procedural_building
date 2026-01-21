# Walls and Corners

## Overview

Walls and corners are now rendered in the debug viewer to provide a more complete visualization of the building structure.

## Walls

### Rendering
- Walls are rendered as vertical rectangles between footprint edge vertices
- Each wall spans from floor base to floor top (z_base to z_base + floor_height)
- **Wall Offset**: Walls are offset slightly inward to make doors and windows more visible from outside

### Parameters

**wall_offset** (default: 0.05m)
- Distance to offset walls inward from the footprint edge
- Exposed in UI as "Wall Offset"
- Typical range: 0.01m - 0.15m
- Allows windows and doors to be visible from outside the building

### Colors
- **Wall color**: Light gray/beige (0.7, 0.7, 0.65, 0.9)
- **Outline**: Darker gray (0.4, 0.4, 0.35)

## Corners

### Rendering
- Corners are rendered at each vertex where two walls meet
- **Two perpendicular rectangles** per corner (not four)
- Each rectangle extends along one of the two adjacent edges
- Corners respect the same wall_offset as walls

### Why Only Two Faces?

Corners only render the two **external** faces for several reasons:
1. **Non-90° angles**: Four-sided corners don't work for arbitrary angles
2. **Visual representation**: This is a visualization, not a full 3D mesh
3. **Performance**: Fewer polygons to render
4. **Clarity**: External faces are what matters for architectural visualization

### Parameters

**corner_size** (default: 0.15m)
- Width of corner element
- Exposed in UI as "Corner Size"
- Typical range: 0.1m - 0.3m
- Larger values create more prominent corner details

### Corner Algorithm

For each vertex:
1. Get previous and next vertices in the polygon
2. Calculate directions to both adjacent vertices
3. Calculate inward normals for proper offset
4. Render two rectangles:
   - One extending toward the previous vertex
   - One extending toward the next vertex

### Colors
- **Corner color**: Darker gray (0.5, 0.5, 0.45, 1.0)
- Creates contrast with wall color

## New Building: Angled House

A new building template with non-orthogonal walls has been added:

**Angled House**:
- Hexagonal-style footprint
- Features 30-60 degree angled walls
- 3 stories
- Demonstrates that the system works with arbitrary polygons

Vertices create a shape with:
- Horizontal bottom edge
- Angled sides (~60 degrees)
- Vertical walls
- Horizontal top edge

## UI Controls

### Visibility Toggles
- **Show Walls**: Toggle wall rendering (default: ON)
- **Show Corners**: Toggle corner rendering (default: ON)

### Parameters
- **Wall Offset**: Distance to offset walls inward (default: 0.05)
- **Corner Size**: Width of corner elements (default: 0.15)

## Visual Hierarchy

Rendering order (back to front):
1. **Walls** (filled rectangles)
2. **Footprint outline** (wireframe)
3. **Corners** (filled darker rectangles)
4. **Doors** (red-orange rectangles with arrows)
5. **Windows** (light blue rectangles)

This ensures elements are properly layered for clear visualization.

## Implementation Notes

### Wall Offset Calculation
```python
# Calculate inward normal (perpendicular to edge)
dx = x2 - x1
dy = y2 - y1
length = sqrt(dx*dx + dy*dy)

# Rotate 90 degrees counterclockwise for CCW polygons
normal_x = -dy / length
normal_y = dx / length

# Offset inward
x_offset = x + normal_x * wall_offset
y_offset = y + normal_y * wall_offset
```

### Corner Placement
Corners use the **average of adjacent edge normals** to determine their inward offset, ensuring corners stay properly positioned even at sharp angles.

## Future Enhancements

- **Thickness parameter**: Give walls actual thickness (render both sides)
- **Material properties**: Different wall materials/textures
- **Corner styles**: Rounded, chamfered, ornate corners
- **Wall openings**: Proper cutouts where doors/windows are placed
- **Interior walls**: Currently only exterior walls are rendered
