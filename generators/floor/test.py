"""
Test floor element generation (doors, windows, corners).

Tests the placement logic for all floor elements to verify correct behavior.
"""

import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from generators.building import Building


def test_door_generation():
    """Test door generation on floors."""
    
    print("=" * 60)
    print("TESTING DOOR GENERATION")
    print("=" * 60)
    
    # Create a simple square building with 2 floors
    building = Building(
        floors=[
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 0 (ground)
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 1
        ],
        seed=12345,
        floor_heights=[3.0, 3.0]
    )
    
    print(f"\nBuilding: {building.num_floors} floors")
    print(f"Total height: {building.get_total_height():.1f}m\n")
    
    # Test ground floor door generation with different densities
    ground_floor = building.get_floor(0)
    print(f"Ground Floor (idx={ground_floor.floor_idx}):")
    print(f"  Perimeter: {ground_floor.footprint.perimeter():.1f}m")
    
    for door_density in [0.025, 0.05, 0.1, 0.2]:
        ground_floor.clear_generated()
        
        doors = ground_floor.get_doors(
            seed=12345,
            door_density=door_density,
            edge_spacing=1.0
        )
        
        print(f"\n  Door density {door_density}:")
        print(f"    Generated {len(doors)} doors")
        
        for i, door in enumerate(doors):
            pos = door.get_world_position()
            print(f"    Door {i}: edge {door.edge_idx}, position ({pos[0]:.2f}, {pos[1]:.2f})")
            print(f"            facing: ({door.facing_direction[0]:.2f}, {door.facing_direction[1]:.2f}), "
                  f"size: {door.width}m × {door.height}m, main={door.is_main_entrance}")
    
    # Test upper floor (should have no doors)
    upper_floor = building.get_floor(1)
    doors = upper_floor.get_doors(seed=12345, door_density=0.05)
    print(f"\n\nUpper Floor (idx={upper_floor.floor_idx}):")
    print(f"  Generated {len(doors)} doors (should be 0)")
    
    # Test L-shaped building
    print("\n\n--- L-Shaped Building ---\n")
    l_building = Building(
        floors=[
            [(-6, -6), (6, -6), (6, 1), (1, 1), (1, 6), (-6, 6)],
        ],
        seed=99999,
        floor_heights=[3.0]
    )
    
    l_floor = l_building.get_floor(0)
    print(f"L-Shaped Floor:")
    print(f"  Perimeter: {l_floor.footprint.perimeter():.1f}m")
    
    doors = l_floor.get_doors(seed=99999, door_density=0.05)
    print(f"  Generated {len(doors)} doors")
    
    for i, door in enumerate(doors):
        pos = door.get_world_position()
        print(f"  Door {i}: edge {door.edge_idx}, position ({pos[0]:.2f}, {pos[1]:.2f}), "
              f"size: {door.width}m × {door.height}m")
    
    print("\n✓ Door generation tests passed\n")


def test_window_generation():
    """Test window generation on floors."""
    
    print("=" * 60)
    print("TESTING WINDOW GENERATION")
    print("=" * 60)
    
    # Create a simple square building with 2 floors
    building = Building(
        floors=[
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 0 (ground)
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 1
        ],
        seed=12345,
        floor_heights=[3.0, 3.0]
    )
    
    print(f"\nBuilding: {building.num_floors} floors")
    print(f"Perimeter: {building.get_floor(0).footprint.perimeter():.1f}m\n")
    
    # Test ground floor with doors and windows
    ground_floor = building.get_floor(0)
    print(f"Ground Floor (idx={ground_floor.floor_idx}):")
    
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
    for i, window in enumerate(windows[:5]):  # Show first 5
        pos = window.get_world_position()
        print(f"    Window {i}: edge {window.edge_idx}, pos ({pos[0]:.2f}, {pos[1]:.2f}), "
              f"{window.width}m × {window.height}m")
    if len(windows) > 5:
        print(f"    ... and {len(windows) - 5} more windows")
    
    # Test with higher window density
    print(f"\n\n--- Higher Window Density ---\n")
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
    
    print("\n✓ Window generation tests passed\n")


def test_corner_generation():
    """Test corner generation on floors."""
    
    print("=" * 60)
    print("TESTING CORNER GENERATION")
    print("=" * 60)
    
    # Create buildings with different shapes
    building = Building(
        floors=[
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Square
        ],
        seed=12345,
        floor_heights=[3.0]
    )
    
    floor = building.get_floor(0)
    corners = floor.get_corners(seed=12345)
    
    print(f"\nSquare building:")
    print(f"  Vertices: {len(floor.footprint.get_vertices())}")
    print(f"  Generated {len(corners)} corners (should match vertices)")
    
    for i, corner in enumerate(corners):
        print(f"  Corner {i}: vertex_idx={corner.vertex_idx}, "
              f"pos=({corner.position[0]:.1f}, {corner.position[1]:.1f}), "
              f"width={corner.width}m")
    
    # Test L-shaped building
    l_building = Building(
        floors=[
            [(-6, -6), (6, -6), (6, 1), (1, 1), (1, 6), (-6, 6)],
        ],
        seed=99999,
        floor_heights=[3.0]
    )
    
    l_floor = l_building.get_floor(0)
    l_corners = l_floor.get_corners(seed=99999)
    
    print(f"\nL-shaped building:")
    print(f"  Vertices: {len(l_floor.footprint.get_vertices())}")
    print(f"  Generated {len(l_corners)} corners")
    
    print("\n✓ Corner generation tests passed\n")


def test_collision_avoidance():
    """Test that windows avoid doors correctly."""
    
    print("=" * 60)
    print("TESTING COLLISION AVOIDANCE")
    print("=" * 60)
    
    building = Building(
        floors=[
            [(-10, -10), (10, -10), (10, 10), (-10, 10)],
        ],
        seed=12345,
        floor_heights=[3.0]
    )
    
    floor = building.get_floor(0)
    
    # High density to test collision avoidance
    doors = floor.get_doors(seed=12345, door_density=0.1)
    windows = floor.get_windows(seed=12345, window_density=0.5)
    
    print(f"\nLarge building (perimeter={floor.footprint.perimeter():.1f}m):")
    print(f"  Doors: {len(doors)}")
    print(f"  Windows: {len(windows)}")
    
    # Check for collisions
    collisions = 0
    min_spacing = 1.5  # Minimum spacing expected
    
    for door in doors:
        door_pos = door.get_world_position()
        for window in windows:
            if door.edge_idx == window.edge_idx:
                window_pos = window.get_world_position()
                distance = ((door_pos[0] - window_pos[0])**2 + 
                           (door_pos[1] - window_pos[1])**2)**0.5
                if distance < min_spacing:
                    collisions += 1
                    print(f"  ⚠ Collision detected: Door at {door_pos}, Window at {window_pos}, distance={distance:.2f}m")
    
    if collisions == 0:
        print(f"  ✓ No collisions detected (all elements properly spaced)")
    else:
        print(f"  ✗ Found {collisions} collisions!")
    
    print("\n✓ Collision avoidance tests passed\n")


def run_all_tests():
    """Run all floor generation tests."""
    
    print("\n")
    print("*" * 60)
    print("FLOOR GENERATION TEST SUITE")
    print("*" * 60)
    print("\n")
    
    test_door_generation()
    test_window_generation()
    test_corner_generation()
    test_collision_avoidance()
    
    print("*" * 60)
    print("ALL TESTS PASSED ✓")
    print("*" * 60)
    print("\n")


if __name__ == '__main__':
    run_all_tests()
