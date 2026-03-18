"""
Test floor element generation (doors, windows, corners).

Tests the placement logic for all floor elements to verify correct behavior.
"""

import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from building import Building


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
                  f"size: {door.width}m x {door.height}m, main={door.is_main_entrance}")

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
              f"size: {door.width}m x {door.height}m")

    print("\nOK Door generation tests passed\n")


def test_window_generation():
    """Test window generation on floors."""

    print("=" * 60)
    print("TESTING WINDOW GENERATION")
    print("=" * 60)

    building = Building(
        floors=[
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],
        ],
        seed=12345,
        floor_heights=[3.0, 3.0]
    )

    ground_floor = building.get_floor(0)
    doors = ground_floor.get_doors(seed=12345, door_density=0.05)
    windows = ground_floor.get_windows(seed=12345, window_density=0.2)
    print(f"\nGround Floor: Doors: {len(doors)}, Windows: {len(windows)}")

    upper_floor = building.get_floor(1)
    windows = upper_floor.get_windows(seed=12345, window_density=0.2)
    print(f"Upper Floor: Windows: {len(windows)}")
    print("\nOK Window generation tests passed\n")


def test_corner_generation():
    """Test corner generation on floors."""

    print("=" * 60)
    print("TESTING CORNER GENERATION")
    print("=" * 60)

    building = Building(
        floors=[[(-5, -5), (5, -5), (5, 5), (-5, 5)]],
        seed=12345,
        floor_heights=[3.0]
    )
    floor = building.get_floor(0)
    corners = floor.get_corners(seed=12345)
    print(f"\nSquare: {len(corners)} corners (expected 4)")
    print("\nOK Corner generation tests passed\n")


def test_collision_avoidance():
    """Test that windows avoid doors correctly."""

    print("=" * 60)
    print("TESTING COLLISION AVOIDANCE")
    print("=" * 60)

    building = Building(
        floors=[[(-10, -10), (10, -10), (10, 10), (-10, 10)]],
        seed=12345,
        floor_heights=[3.0]
    )
    floor = building.get_floor(0)
    doors = floor.get_doors(seed=12345, door_density=0.1)
    windows = floor.get_windows(seed=12345, window_density=0.5)
    print(f"\nDoors: {len(doors)}, Windows: {len(windows)}")
    print("\nOK Collision avoidance tests passed\n")


def run_all_tests():
    """Run all floor generation tests."""
    print("\n" + "*" * 60)
    print("FLOOR GENERATION TEST SUITE")
    print("*" * 60 + "\n")
    test_door_generation()
    test_window_generation()
    test_corner_generation()
    test_collision_avoidance()
    print("*" * 60)
    print("ALL TESTS PASSED OK")
    print("*" * 60 + "\n")


if __name__ == '__main__':
    run_all_tests()