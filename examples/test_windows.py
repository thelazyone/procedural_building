"""
Test window generation.

Verifies window placement logic works correctly with doors.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.building import Building
from core.floor import Floor

def test_window_generation():
    """Test window generation on a building with doors."""
    
    # Create a simple square building with 2 floors
    building = Building(
        floors=[
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 0 (ground)
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 1
        ],
        seed=12345,
        floor_heights=[3.0, 3.0]
    )
    
    print("=== Testing Window Generation ===\n")
    print(f"Building: {building.num_floors} floors")
    print(f"Perimeter: {building.get_floor(0).footprint.perimeter():.1f}m\n")
    
    # Test ground floor with doors and windows
    ground_floor = building.get_floor(0)
    print(f"Ground Floor (idx={ground_floor.floor_idx}):")
    
    # Get doors and windows
    doors = ground_floor.get_doors(seed=12345, door_density=0.05)
    windows = ground_floor.get_windows(seed=12345, window_density=0.2)
    
    print(f"  Doors: {len(doors)}")
    for i, door in enumerate(doors):
        pos = door.get_world_position()
        print(f"    Door {i}: edge {door.edge_idx}, pos ({pos[0]:.2f}, {pos[1]:.2f}), "
              f"{door.width}m × {door.height}m")
    
    print(f"\n  Windows: {len(windows)}")
    for i, window in enumerate(windows):
        pos = window.get_world_position()
        print(f"    Window {i}: edge {window.edge_idx}, pos ({pos[0]:.2f}, {pos[1]:.2f}), "
              f"{window.width}m × {window.height}m, elev {window.elevation}m")
    
    # Test upper floor (only windows, no doors)
    print(f"\n\nUpper Floor (idx=1):")
    upper_floor = building.get_floor(1)
    
    doors = upper_floor.get_doors(seed=12345, door_density=0.05)
    windows = upper_floor.get_windows(seed=12345, window_density=0.2)
    
    print(f"  Doors: {len(doors)} (should be 0)")
    print(f"  Windows: {len(windows)}")
    for i, window in enumerate(windows):
        pos = window.get_world_position()
        print(f"    Window {i}: edge {window.edge_idx}, pos ({pos[0]:.2f}, {pos[1]:.2f}), "
              f"{window.width}m × {window.height}m")
    
    # Test with higher window density
    print(f"\n\n=== Testing Higher Window Density ===\n")
    ground_floor.clear_generated()
    
    doors = ground_floor.get_doors(seed=12345, door_density=0.05)
    windows = ground_floor.get_windows(seed=12345, window_density=0.5)
    
    print(f"Ground Floor with window_density=0.5:")
    print(f"  Doors: {len(doors)}")
    print(f"  Windows: {len(windows)}")
    print(f"\n  Window distribution by edge:")
    
    edge_counts = {}
    for window in windows:
        edge_counts[window.edge_idx] = edge_counts.get(window.edge_idx, 0) + 1
    
    for edge_idx, count in sorted(edge_counts.items()):
        print(f"    Edge {edge_idx}: {count} windows")


if __name__ == '__main__':
    test_window_generation()
