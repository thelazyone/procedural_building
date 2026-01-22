"""
Door placement logic for floors.

Contains the logic for determining WHERE doors should be placed on a floor,
including spacing, collision avoidance, and density calculations.
"""

import math
import random
from typing import List, Tuple
from core.floor import Floor
from core.footprint import Point2D
from generators.door import Door, DoorGenerator


def generate_doors(
    floor: Floor,
    seed: int,
    door_density: float = 0.05,
    edge_spacing: float = 1.0,
    door_spacing: float = 2.0,
    **params
) -> Tuple[List[Door], List[List[Tuple[float, float]]]]:
    """
    Generate doors for a floor based on placement logic.
    
    This function determines WHERE doors should be placed (spacing, density, etc.)
    and creates Door objects with properties from DoorGenerator.
    
    Args:
        floor: Floor object to generate doors for
        seed: Generation seed
        door_density: Number of doors per meter of perimeter
        edge_spacing: Minimum spacing from edge corners (meters)
        door_spacing: Minimum spacing between doors (meters)
        **params: Additional parameters passed to DoorGenerator
        
    Returns:
        Tuple of (List of Door objects, occupied segments for collision avoidance)
    """
    # Only generate doors on ground floor
    if floor.floor_idx != 0:
        # Return empty doors and empty occupied segments (one per edge)
        edges = floor.footprint.get_edges()
        empty_segments = [[] for _ in range(len(edges))]
        return [], empty_segments
    
    rng = random.Random(seed)
    footprint = floor.footprint
    edges = footprint.get_edges()
    
    # Calculate total perimeter and edge lengths
    edge_lengths = []
    total_perimeter = 0.0
    for edge_start, edge_end in edges:
        dx = edge_end[0] - edge_start[0]
        dy = edge_end[1] - edge_start[1]
        length = math.sqrt(dx * dx + dy * dy)
        edge_lengths.append(length)
        total_perimeter += length
    
    # Calculate number of doors based on density
    num_doors = max(1, int(total_perimeter * door_density))
    
    # Track occupied segments on each edge: list of (start_pos, end_pos) tuples
    occupied_segments = [[] for _ in range(len(edges))]
    
    doors = []
    door_generator = DoorGenerator()
    attempts_per_door = 10  # Max attempts to place each door
    
    for door_idx in range(num_doors):
        placed = False
        
        for attempt in range(attempts_per_door):
            # Pick a random edge weighted by edge length
            edge_idx = _weighted_random_choice(rng, edge_lengths)
            edge_start, edge_end = edges[edge_idx]
            edge_length = edge_lengths[edge_idx]
            
            # Check if edge is long enough for door placement
            available_length = edge_length - 2 * edge_spacing
            if available_length < 0.5:  # Need at least 0.5m for door
                continue
            
            # Pick random position along edge (avoiding edge_spacing from ends)
            normalized_spacing = edge_spacing / edge_length
            target_position = rng.uniform(normalized_spacing, 1.0 - normalized_spacing)
            
            # Convert to absolute position along edge (in meters)
            abs_position = target_position * edge_length
            
            # Check collision with existing doors on this edge
            collision = False
            for occupied_start, occupied_end in occupied_segments[edge_idx]:
                if not (abs_position + door_spacing / 2 < occupied_start or 
                        abs_position - door_spacing / 2 > occupied_end):
                    collision = True
                    break
            
            if not collision:
                # Position is valid, place door here
                placed = True
            else:
                # Try to find closest valid position
                valid_position = _find_closest_valid_position(
                    abs_position, edge_length, occupied_segments[edge_idx],
                    edge_spacing, door_spacing
                )
                
                if valid_position is not None:
                    target_position = valid_position / edge_length
                    abs_position = valid_position
                    placed = True
                else:
                    # No valid position found, try another edge
                    continue
            
            if placed:
                # Mark this segment as occupied
                occupied_start = abs_position - door_spacing / 2
                occupied_end = abs_position + door_spacing / 2
                occupied_segments[edge_idx].append((occupied_start, occupied_end))
                
                # Calculate facing direction (outward normal)
                edge_dx = edge_end[0] - edge_start[0]
                edge_dy = edge_end[1] - edge_start[1]
                edge_len = math.sqrt(edge_dx * edge_dx + edge_dy * edge_dy)
                
                # Perpendicular to edge (rotated 90 degrees clockwise for outward normal)
                normal_x = edge_dy / edge_len
                normal_y = -edge_dx / edge_len
                
                # Generate door properties
                door_seed = hash((seed, "door", door_idx)) % (2**31)
                door_props = door_generator.generate(
                    parent_context=floor,
                    seed=door_seed,
                    door_idx=door_idx,
                    total_doors=num_doors,
                    **params
                )
                
                # Create complete Door object
                door = Door(
                    edge_idx=edge_idx,
                    position_on_edge=target_position,
                    edge_start=edge_start,
                    edge_end=edge_end,
                    facing_direction=(normal_x, normal_y),
                    floor_idx=floor.floor_idx,
                    properties=door_props
                )
                doors.append(door)
                break
        
        # If we couldn't place this door after all attempts, skip it
        if not placed:
            print(f"Warning: Could not place door {door_idx + 1}, skipping")
    
    return doors, occupied_segments


def _find_closest_valid_position(
    target_pos: float,
    edge_length: float,
    occupied_segments: List[Tuple[float, float]],
    edge_spacing: float,
    door_spacing: float
) -> float:
    """
    Find the closest valid position to target_pos that doesn't collide.
    
    Args:
        target_pos: Desired position along edge (meters)
        edge_length: Total length of edge (meters)
        occupied_segments: List of (start, end) tuples of occupied segments
        edge_spacing: Min distance from edge ends
        door_spacing: Min spacing between doors
        
    Returns:
        Valid position in meters, or None if no valid position exists
    """
    # Try positions in both directions from target
    search_distance = door_spacing
    best_position = None
    best_distance = float('inf')
    
    # Search in steps of 0.1m
    step = 0.1
    for offset in range(int(search_distance / step) + 1):
        for direction in [1, -1]:
            if offset == 0 and direction == -1:
                continue  # Skip duplicate at offset=0
            
            test_pos = target_pos + direction * offset * step
            
            # Check bounds
            if test_pos < edge_spacing or test_pos > edge_length - edge_spacing:
                continue
            
            # Check collision with all occupied segments
            valid = True
            for occupied_start, occupied_end in occupied_segments:
                if not (test_pos + door_spacing / 2 < occupied_start or 
                        test_pos - door_spacing / 2 > occupied_end):
                    valid = False
                    break
            
            if valid:
                distance = abs(test_pos - target_pos)
                if distance < best_distance:
                    best_distance = distance
                    best_position = test_pos
    
    return best_position


def _weighted_random_choice(rng: random.Random, weights: List[float]) -> int:
    """
    Choose random index weighted by values.
    
    Args:
        rng: Random number generator
        weights: List of weights
        
    Returns:
        Selected index
    """
    total = sum(weights)
    r = rng.uniform(0, total)
    
    cumulative = 0.0
    for i, weight in enumerate(weights):
        cumulative += weight
        if r <= cumulative:
            return i
    
    return len(weights) - 1  # Fallback
