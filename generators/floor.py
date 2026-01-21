"""
Floor generator.

Generates doors, windows, and other floor elements based on footprint and parameters.
Handles PLACEMENT logic - calls sub-generators for properties.
"""

import math
import random
from typing import List, Tuple, Optional
from core.generator_base import GeneratorBase
from core.floor import Floor
from core.footprint import Point2D
from .door import DoorGenerator, DoorProperties


class Door:
    """
    Complete door representation: placement + properties.
    
    Created by FloorGenerator by combining placement logic with 
    properties from DoorGenerator.
    """
    
    def __init__(
        self,
        edge_idx: int,
        position_on_edge: float,
        edge_start: Point2D,
        edge_end: Point2D,
        facing_direction: Tuple[float, float],
        floor_idx: int,
        properties: DoorProperties
    ):
        """
        Initialize door.
        
        Args:
            edge_idx: Index of the edge this door is on
            position_on_edge: Position along edge (0.0 = start, 1.0 = end)
            edge_start: Start point of the edge
            edge_end: End point of the edge
            facing_direction: Normalized direction the door faces (outward normal)
            floor_idx: Floor index
            properties: Door properties (size, style, etc.)
        """
        self.edge_idx = edge_idx
        self.position_on_edge = position_on_edge
        self.edge_start = edge_start
        self.edge_end = edge_end
        self.facing_direction = facing_direction
        self.floor_idx = floor_idx
        self.properties = properties
    
    def get_world_position(self) -> Point2D:
        """Calculate actual world (x, y) position of door center."""
        x = self.edge_start[0] + (self.edge_end[0] - self.edge_start[0]) * self.position_on_edge
        y = self.edge_start[1] + (self.edge_end[1] - self.edge_start[1]) * self.position_on_edge
        return (x, y)
    
    @property
    def width(self) -> float:
        """Door width."""
        return self.properties.width
    
    @property
    def height(self) -> float:
        """Door height."""
        return self.properties.height
    
    @property
    def is_main_entrance(self) -> bool:
        """Whether this is the main entrance."""
        return self.properties.is_main_entrance


class DoorPlacement:
    """
    Represents a door placement along a footprint edge.
    
    This is the intermediate representation before creating the Door object.
    """
    
    def __init__(
        self,
        edge_idx: int,
        position_on_edge: float,  # 0.0 to 1.0 along the edge
        edge_start: Point2D,
        edge_end: Point2D,
        facing_direction: Tuple[float, float],  # Normalized 2D vector
        floor_idx: int
    ):
        """
        Initialize door placement.
        
        Args:
            edge_idx: Index of the edge this door is on
            position_on_edge: Position along edge (0.0 = start, 1.0 = end)
            edge_start: Start point of the edge
            edge_end: End point of the edge
            facing_direction: Normalized direction the door faces (outward normal)
            floor_idx: Floor index
        """
        self.edge_idx = edge_idx
        self.position_on_edge = position_on_edge
        self.edge_start = edge_start
        self.edge_end = edge_end
        self.facing_direction = facing_direction
        self.floor_idx = floor_idx


class FloorGenerator(GeneratorBase):
    """
    Generates floor elements (doors, windows, etc.) based on floor footprint.
    """
    
    def generate(
        self,
        parent_context: Floor,
        seed: int,
        door_density: float = 0.05,  # Doors per meter of perimeter
        window_density: float = 0.3,  # Windows per meter of perimeter
        edge_spacing: float = 1.0,  # Min distance from edge corners
        **params
    ) -> dict:
        """
        Generate all floor elements.
        
        Args:
            parent_context: Floor object
            seed: Generation seed
            door_density: Number of doors per meter of perimeter
            window_density: Number of windows per meter of perimeter
            edge_spacing: Minimum spacing from edge ends for door placement
            **params: Additional parameters
            
        Returns:
            Dictionary with 'doors' and 'windows' lists
        """
        floor = parent_context
        rng = random.Random(seed)
        
        # Generate doors (only on ground floor for now)
        doors = []
        if floor.floor_idx == 0:
            door_placements = self._generate_door_placements(
                floor, rng, door_density, edge_spacing
            )
            
            # Generate door properties for each placement
            door_generator = DoorGenerator()
            for i, placement in enumerate(door_placements):
                # Derive seed for this specific door
                door_seed = self.derive_seed(seed, f"door_{i}")
                
                # Get door properties from door generator
                door_props = door_generator.generate(
                    parent_context=floor,
                    seed=door_seed,
                    door_idx=i,
                    total_doors=len(door_placements),
                    **params
                )
                
                # Create complete Door object combining placement + properties
                door = Door(
                    edge_idx=placement.edge_idx,
                    position_on_edge=placement.position_on_edge,
                    edge_start=placement.edge_start,
                    edge_end=placement.edge_end,
                    facing_direction=placement.facing_direction,
                    floor_idx=placement.floor_idx,
                    properties=door_props
                )
                doors.append(door)
        
        # TODO: Generate windows (future implementation)
        windows = []
        
        return {
            'doors': doors,
            'windows': windows
        }
    
    def _generate_door_placements(
        self,
        floor: Floor,
        rng: random.Random,
        door_density: float,
        edge_spacing: float,
        door_spacing: float = 2.0  # Min spacing between doors
    ) -> List[DoorPlacement]:
        """
        Generate door placements along floor perimeter with collision avoidance.
        
        Args:
            floor: Floor object
            rng: Random number generator
            door_density: Doors per meter of perimeter
            edge_spacing: Min distance from edge corners (meters)
            door_spacing: Min distance between doors (meters)
            
        Returns:
            List of DoorPlacement objects
        """
        footprint = floor.footprint
        vertices = footprint.get_vertices()
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
        
        placements = []
        attempts_per_door = 10  # Max attempts to place each door
        
        for door_idx in range(num_doors):
            placed = False
            
            for attempt in range(attempts_per_door):
                # Pick a random edge weighted by edge length
                edge_idx = self._weighted_random_choice(rng, edge_lengths)
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
                    valid_position = self._find_closest_valid_position(
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
                    
                    placement = DoorPlacement(
                        edge_idx=edge_idx,
                        position_on_edge=target_position,
                        edge_start=edge_start,
                        edge_end=edge_end,
                        facing_direction=(normal_x, normal_y),
                        floor_idx=floor.floor_idx
                    )
                    placements.append(placement)
                    break
            
            # If we couldn't place this door after all attempts, skip it
            if not placed:
                print(f"Warning: Could not place door {door_idx + 1}, skipping")
        
        return placements
    
    def _find_closest_valid_position(
        self,
        target_pos: float,
        edge_length: float,
        occupied_segments: List[Tuple[float, float]],
        edge_spacing: float,
        door_spacing: float
    ) -> Optional[float]:
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
    
    def _weighted_random_choice(
        self,
        rng: random.Random,
        weights: List[float]
    ) -> int:
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
