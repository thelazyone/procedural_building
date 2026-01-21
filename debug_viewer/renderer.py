"""
3D renderer for building visualization.

Handles OpenGL rendering of building elements.
"""

from typing import List, Tuple
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
import os

# Add parent directory to path to import procedural_building
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.building import Building
from core.footprint import Point2D


class BuildingRenderer:
    """
    Renders building structures in 3D.
    
    For MVP: renders floor footprints as flat polygons at different heights.
    """
    
    def __init__(self):
        """Initialize renderer."""
        self.show_footprints = True
        self.show_walls = False
        self.show_windows = False
        self.show_doors = True
        self.show_corners = False
        
        # Colors
        self.footprint_color = (0.3, 0.5, 0.8, 0.6)  # Blue with transparency
        self.grid_color = (0.3, 0.3, 0.3, 1.0)
        self.door_color = (0.8, 0.3, 0.2, 0.9)  # Red-orange
        self.main_entrance_color = (0.9, 0.5, 0.1, 1.0)  # Brighter orange
    
    def setup_gl(self, width: int, height: int):
        """Setup OpenGL state."""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Smooth shading
        glShadeModel(GL_SMOOTH)
        
        # Background color (dark gray)
        glClearColor(0.15, 0.15, 0.15, 1.0)
    
    def render_grid(self, size: float = 50.0, step: float = 5.0):
        """Render ground grid."""
        glColor4f(*self.grid_color)
        glBegin(GL_LINES)
        
        half_size = size / 2
        num_lines = int(size / step) + 1
        
        for i in range(num_lines):
            offset = -half_size + i * step
            
            # Lines parallel to X axis
            glVertex3f(-half_size, offset, 0)
            glVertex3f(half_size, offset, 0)
            
            # Lines parallel to Y axis
            glVertex3f(offset, -half_size, 0)
            glVertex3f(offset, half_size, 0)
        
        glEnd()
    
    def render_footprint(
        self,
        vertices: List[Point2D],
        z_base: float,
        z_top: float
    ):
        """
        Render a single footprint as a flat polygon.
        
        Args:
            vertices: List of (x, y) vertices
            z_base: Base Z height
            z_top: Top Z height (for future wall rendering)
        """
        if not self.show_footprints:
            return
        
        # Render bottom face
        glColor4f(*self.footprint_color)
        glBegin(GL_POLYGON)
        for x, y in vertices:
            glVertex3f(x, y, z_base)
        glEnd()
        
        # Render outline
        glLineWidth(2.0)
        glColor4f(0.2, 0.3, 0.5, 1.0)  # Darker blue
        glBegin(GL_LINE_LOOP)
        for x, y in vertices:
            glVertex3f(x, y, z_base)
        glEnd()
        glLineWidth(1.0)
    
    def render_door(self, door, z_base: float):
        """
        Render a door as a vertical rectangle.
        
        Args:
            door: Door object with position and properties
            z_base: Base Z height of the floor
        """
        if not self.show_doors:
            return
        
        # Get door position
        pos = door.get_world_position()
        x, y = pos
        
        # Door dimensions
        width = door.width
        height = door.height
        
        # Calculate door orientation (perpendicular to facing direction)
        facing_x, facing_y = door.facing_direction
        # Door width direction is perpendicular to facing
        width_x = -facing_y
        width_y = facing_x
        
        # Calculate door corners (slightly inset from wall for visibility)
        inset = 0.05  # 5cm inset from wall
        x_inset = x - facing_x * inset
        y_inset = y - facing_y * inset
        
        # Door corners (4 corners of rectangle)
        hw = width / 2.0  # half width
        corners = [
            (x_inset - width_x * hw, y_inset - width_y * hw, z_base),
            (x_inset + width_x * hw, y_inset + width_y * hw, z_base),
            (x_inset + width_x * hw, y_inset + width_y * hw, z_base + height),
            (x_inset - width_x * hw, y_inset - width_y * hw, z_base + height),
        ]
        
        # Choose color based on whether it's main entrance
        if door.is_main_entrance:
            color = self.main_entrance_color
        else:
            color = self.door_color
        
        # Render door as filled rectangle
        glColor4f(*color)
        glBegin(GL_QUADS)
        for corner in corners:
            glVertex3f(*corner)
        glEnd()
        
        # Render door outline
        glLineWidth(2.0)
        glColor4f(0.6, 0.2, 0.1, 1.0)  # Darker outline
        glBegin(GL_LINE_LOOP)
        for corner in corners:
            glVertex3f(*corner)
        glEnd()
        glLineWidth(1.0)
        
        # Render facing direction arrow (short line pointing outward)
        arrow_length = 0.5
        arrow_end_x = x + facing_x * arrow_length
        arrow_end_y = y + facing_y * arrow_length
        
        glLineWidth(3.0)
        glColor4f(1.0, 1.0, 0.0, 1.0)  # Yellow arrow
        glBegin(GL_LINES)
        glVertex3f(x, y, z_base + height / 2)
        glVertex3f(arrow_end_x, arrow_end_y, z_base + height / 2)
        glEnd()
        glLineWidth(1.0)
    
    def render_building(self, building: Building, generation_params: dict = None):
        """
        Render entire building.
        
        Args:
            building: Building object to render
            generation_params: Parameters to pass to floor generation (door_density, etc.)
        """
        if building is None:
            return
        
        if generation_params is None:
            generation_params = {}
        
        # Render each floor
        for floor_idx in range(building.num_floors):
            floor = building.get_floor(floor_idx)
            z_base = building.get_floor_z_base(floor_idx)
            z_top = building.get_floor_z_top(floor_idx)
            
            vertices = floor.footprint.get_vertices()
            self.render_footprint(vertices, z_base, z_top)
            
            # Render doors for this floor
            if self.show_doors:
                doors = floor.get_doors(
                    seed=building.seed,
                    **generation_params
                )
                for door in doors:
                    self.render_door(door, z_base)
    
    def render_scene(self, building: Building = None):
        """
        Render complete scene.
        
        NOTE: This method no longer clears the buffer - that's done in the viewer.
        
        Args:
            building: Optional building to render
        """
        # Render grid
        self.render_grid()
        
        # Render building if present
        if building is not None:
            self.render_building(building)
