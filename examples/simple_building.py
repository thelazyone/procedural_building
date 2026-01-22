"""
Simple example: Create and inspect a basic building.

This demonstrates the core API without the debug viewer.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generators.building import Building
from generators.floor.floor import Floor
from core.footprint import Footprint


def main():
    """Create and inspect a simple building."""
    
    print("=== Simple Building Example ===\n")
    
    # Method 1: Create building from vertex lists
    print("Method 1: Building from vertex lists")
    floor_plans = [
        [(0, 0), (10, 0), (10, 10), (0, 10)],  # Floor 1
        [(0, 0), (10, 0), (10, 10), (0, 10)],  # Floor 2
        [(0, 0), (10, 0), (10, 10), (0, 10)],  # Floor 3
    ]
    
    building = Building(
        floors=floor_plans,
        seed=12345,
        floor_heights=[3.0, 3.0, 3.0]
    )
    
    print(f"  Number of floors: {building.num_floors}")
    print(f"  Total height: {building.get_total_height():.1f}m")
    
    # Inspect each floor
    for i in range(building.num_floors):
        floor = building.get_floor(i)
        z_base = building.get_floor_z_base(i)
        z_top = building.get_floor_z_top(i)
        
        print(f"\n  Floor {i}:")
        print(f"    Height: {floor.height:.1f}m")
        print(f"    Z range: {z_base:.1f}m to {z_top:.1f}m")
        print(f"    Area: {floor.footprint.area():.1f}m²")
        print(f"    Perimeter: {floor.footprint.perimeter():.1f}m")
        print(f"    Vertices: {len(floor.footprint.get_vertices())}")
    
    print("\n" + "="*40 + "\n")
    
    # Method 2: Create building from Floor objects
    print("Method 2: Building from Floor objects")
    
    floors = [
        Floor.from_vertices([(0, 0), (8, 0), (8, 8), (0, 8)], height=3.5, floor_idx=0),
        Floor.from_vertices([(0, 0), (8, 0), (8, 8), (0, 8)], height=3.0, floor_idx=1),
    ]
    
    building2 = Building(floors=floors, seed=54321)
    
    print(f"  Number of floors: {building2.num_floors}")
    print(f"  Total height: {building2.get_total_height():.1f}m")
    
    print("\n" + "="*40 + "\n")
    
    # Method 3: Non-convex footprint (L-shaped building)
    print("Method 3: Non-convex L-shaped building")
    
    l_shaped = [
        (0, 0), (10, 0), (10, 5), (5, 5),
        (5, 10), (0, 10)
    ]
    
    building3 = Building(
        floors=[l_shaped, l_shaped],
        seed=99999,
        floor_heights=[3.0, 3.0]
    )
    
    floor_0 = building3.get_floor(0)
    print(f"  L-shaped footprint area: {floor_0.footprint.area():.1f}m²")
    print(f"  Perimeter: {floor_0.footprint.perimeter():.1f}m")
    print(f"  Number of edges: {len(floor_0.footprint.get_edges())}")
    
    # Show edges
    print(f"  Edges:")
    for i, (start, end) in enumerate(floor_0.footprint.get_edges()):
        print(f"    {i}: {start} -> {end}")
    
    print("\nDone!")


if __name__ == '__main__':
    main()
