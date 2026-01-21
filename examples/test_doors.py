"""
Test door generation.

Simple example to verify door placement logic works correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.building import Building
from core.floor import Floor

def test_door_generation():
    """Test door generation on a simple building."""
    
    # Create a simple square building with 2 floors
    building = Building(
        floors=[
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 0 (ground)
            [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 1
        ],
        seed=12345,
        floor_heights=[3.0, 3.0]
    )
    
    print("=== Testing Door Generation ===\n")
    print(f"Building: {building.num_floors} floors")
    print(f"Total height: {building.get_total_height():.1f}m\n")
    
    # Test ground floor door generation
    ground_floor = building.get_floor(0)
    print(f"Ground Floor (idx={ground_floor.floor_idx}):")
    print(f"  Perimeter: {ground_floor.footprint.perimeter():.1f}m")
    
    # Generate doors with different densities
    for door_density in [0.025, 0.05, 0.1, 0.2]:
        # Clear cached generation to test with new density
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
    print("\n\n=== Testing L-Shaped Building ===\n")
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


if __name__ == '__main__':
    test_door_generation()
