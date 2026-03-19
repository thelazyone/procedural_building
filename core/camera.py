"""
Orbit camera for 3D visualization.

Provides mouse-controlled orbit camera around a target point.
Shared by building_viewer and block_viewer.
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
    - Middle mouse drag: Pan (move orbit target in the view plane)
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
        self.is_panning = False
        self.last_mouse_pos = (0, 0)
        self.rotation_speed = 0.3
        self.zoom_speed = 1.0
        self.pan_speed = 0.0011  # scales with distance; lower = slower pan

    def handle_mouse_down(self, pos: Tuple[int, int], button: int):
        """Handle mouse button press."""
        if button == 1:  # Left button
            self.is_dragging = True
            self.last_mouse_pos = pos
        elif button == 2:  # Middle button (wheel click)
            self.is_panning = True
            self.last_mouse_pos = pos

    def handle_mouse_up(self, pos: Tuple[int, int], button: int):
        """Handle mouse button release."""
        if button == 1:  # Left button
            self.is_dragging = False
        elif button == 2:
            self.is_panning = False

    def _pan_from_mouse_delta(self, dx: float, dy: float) -> None:
        """
        Move orbit target in the view plane (gluLookAt basis: side, up).

        Screen x increases to the right; screen y increases downward (pygame).
        """
        px, py, pz = self.get_position()
        tx, ty, tz = self.target
        fx = tx - px
        fy = ty - py
        fz = tz - pz
        flen = math.sqrt(fx * fx + fy * fy + fz * fz)
        if flen < 1e-9:
            return
        fx /= flen
        fy /= flen
        fz /= flen

        # side = cross(forward, world_up), matches gluLookAt-style frame (Z-up world)
        sx = fy * 1.0 - fz * 0.0
        sy = fz * 0.0 - fx * 1.0
        sz = fx * 0.0 - fy * 0.0
        slen = math.sqrt(sx * sx + sy * sy + sz * sz)
        if slen < 1e-9:
            sx, sy, sz = 1.0, 0.0, 0.0
        else:
            sx /= slen
            sy /= slen
            sz /= slen

        # up_cam = cross(side, forward)
        ux = sy * fz - sz * fy
        uy = sz * fx - sx * fz
        uz = sx * fy - sy * fx
        ulen = math.sqrt(ux * ux + uy * uy + uz * uz)
        if ulen < 1e-9:
            return
        ux /= ulen
        uy /= ulen
        uz /= ulen

        scale = self.pan_speed * self.distance
        # Grab-the-scene: drag direction matches how content moves under the cursor
        self.target[0] += -sx * dx * scale + ux * dy * scale
        self.target[1] += -sy * dx * scale + uy * dy * scale
        self.target[2] += -sz * dx * scale + uz * dy * scale

    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse movement."""
        if self.is_dragging:
            dx = pos[0] - self.last_mouse_pos[0]
            dy = pos[1] - self.last_mouse_pos[1]

            self.azimuth += dx * self.rotation_speed
            self.elevation += dy * self.rotation_speed

            self.elevation = max(self.min_elevation, min(self.max_elevation, self.elevation))

            self.azimuth = self.azimuth % 360

            self.last_mouse_pos = pos
        elif self.is_panning:
            dx = pos[0] - self.last_mouse_pos[0]
            dy = pos[1] - self.last_mouse_pos[1]
            self._pan_from_mouse_delta(float(dx), float(dy))
            self.last_mouse_pos = pos

    def handle_mouse_wheel(self, delta: int):
        """Handle mouse wheel scroll."""
        self.distance -= delta * self.zoom_speed
        self.distance = max(self.min_distance, min(self.max_distance, self.distance))

    def get_position(self) -> Tuple[float, float, float]:
        """
        Calculate camera position in world space.

        Returns:
            (x, y, z) camera position
        """
        az_rad = math.radians(self.azimuth)
        el_rad = math.radians(self.elevation)

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
