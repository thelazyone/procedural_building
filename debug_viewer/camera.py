"""
Orbit camera for 3D visualization.

Provides mouse-controlled orbit camera around a target point.
"""

import math
from typing import Tuple
from OpenGL.GL import *
from OpenGL.GLU import *


class OrbitCamera:
    """
    Orbit camera that rotates around a target point.
    
    Controls:
    - Left mouse drag: Rotate around target
    - Scroll: Zoom in/out
    """
    
    def __init__(
        self,
        target: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        distance: float = 20.0,
        azimuth: float = 45.0,
        elevation: float = 30.0
    ):
        """
        Initialize orbit camera.
        
        Args:
            target: Point to orbit around (x, y, z)
            distance: Distance from target
            azimuth: Horizontal angle in degrees
            elevation: Vertical angle in degrees
        """
        self.target = list(target)
        self.distance = distance
        self.azimuth = azimuth  # Horizontal rotation
        self.elevation = elevation  # Vertical rotation
        
        # Limits
        self.min_distance = 1.0
        self.max_distance = 100.0
        self.min_elevation = -89.0
        self.max_elevation = 89.0
        
        # Mouse interaction
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)
        self.rotation_speed = 0.3
        self.zoom_speed = 1.0
    
    def handle_mouse_down(self, pos: Tuple[int, int], button: int):
        """Handle mouse button press."""
        if button == 1:  # Left button
            self.is_dragging = True
            self.last_mouse_pos = pos
    
    def handle_mouse_up(self, pos: Tuple[int, int], button: int):
        """Handle mouse button release."""
        if button == 1:  # Left button
            self.is_dragging = False
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse movement."""
        if self.is_dragging:
            dx = pos[0] - self.last_mouse_pos[0]
            dy = pos[1] - self.last_mouse_pos[1]
            
            # Update angles (+ for azimuth to rotate in intuitive direction)
            self.azimuth += dx * self.rotation_speed
            self.elevation += dy * self.rotation_speed
            
            # Clamp elevation
            self.elevation = max(self.min_elevation, min(self.max_elevation, self.elevation))
            
            # Normalize azimuth to [0, 360)
            self.azimuth = self.azimuth % 360
            
            self.last_mouse_pos = pos
    
    def handle_mouse_wheel(self, delta: int):
        """Handle mouse wheel scroll."""
        # Zoom in/out
        self.distance -= delta * self.zoom_speed
        self.distance = max(self.min_distance, min(self.max_distance, self.distance))
    
    def get_position(self) -> Tuple[float, float, float]:
        """
        Calculate camera position in world space.
        
        Returns:
            (x, y, z) camera position
        """
        # Convert to radians
        az_rad = math.radians(self.azimuth)
        el_rad = math.radians(self.elevation)
        
        # Calculate position on sphere
        x = self.target[0] + self.distance * math.cos(el_rad) * math.sin(az_rad)
        y = self.target[1] + self.distance * math.cos(el_rad) * math.cos(az_rad)
        z = self.target[2] + self.distance * math.sin(el_rad)
        
        return (x, y, z)
    
    def apply(self):
        """Apply camera transformation to OpenGL."""
        pos = self.get_position()
        gluLookAt(
            pos[0], pos[1], pos[2],  # Camera position
            self.target[0], self.target[1], self.target[2],  # Look at target
            0, 0, 1  # Up vector (Z-up)
        )
