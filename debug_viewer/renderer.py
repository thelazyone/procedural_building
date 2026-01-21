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
        self.show_walls = True
        self.show_windows = True
        self.show_doors = True
        self.show_corners = True
        
        # Colors
        self.footprint_color = (0.3, 0.5, 0.8, 0.6)  # Blue with transparency
        self.grid_color = (0.3, 0.3, 0.3, 1.0)
        self.door_color = (0.8, 0.3, 0.2, 0.9)  # Red-orange
        self.main_entrance_color = (0.9, 0.5, 0.1, 1.0)  # Brighter orange
        self.window_color = (0.6, 0.8, 0.9, 0.8)  # Light blue with transparency
        self.wall_color = (0.7, 0.7, 0.65, 0.9)  # Light gray/beige
        self.corner_color = (0.5, 0.5, 0.45, 1.0)  # Darker gray for corners
    
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
        
        # Door endpoints
        hw = width / 2.0  # half width
        x1 = x_inset - width_x * hw
        y1 = y_inset - width_y * hw
        x2 = x_inset + width_x * hw
        y2 = y_inset + width_y * hw
        
        # Choose color based on whether it's main entrance
        if door.is_main_entrance:
            color = self.main_entrance_color
        else:
            color = self.door_color
        
        # Use helper function to render door rectangle
        self.render_vertical_rectangle(
            x1, y1, x2, y2,
            z_base, z_base + height,
            color,
            outline_color=(0.6, 0.2, 0.1, 1.0),
            outline_width=2.0
        )
        
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
    
    def render_vertical_rectangle(self, x1: float, y1: float, x2: float, y2: float, 
                                  z_bottom: float, z_top: float, 
                                  color: tuple, outline_color: tuple = None, 
                                  outline_width: float = 1.0):
        """
        Render a vertical rectangle between two 2D points.
        
        Args:
            x1, y1: Start point (bottom-left in 2D)
            x2, y2: End point (bottom-right in 2D)
            z_bottom: Bottom Z coordinate
            z_top: Top Z coordinate
            color: RGBA color tuple for fill
            outline_color: Optional RGBA color for outline (None = no outline)
            outline_width: Width of outline
        """
        # Render filled rectangle
        glColor4f(*color)
        glBegin(GL_QUADS)
        glVertex3f(x1, y1, z_bottom)
        glVertex3f(x2, y2, z_bottom)
        glVertex3f(x2, y2, z_top)
        glVertex3f(x1, y1, z_top)
        glEnd()
        
        # Render outline if specified
        if outline_color is not None:
            glLineWidth(outline_width)
            glColor4f(*outline_color)
            glBegin(GL_LINE_LOOP)
            glVertex3f(x1, y1, z_bottom)
            glVertex3f(x2, y2, z_bottom)
            glVertex3f(x2, y2, z_top)
            glVertex3f(x1, y1, z_top)
            glEnd()
            glLineWidth(1.0)
    
    def render_wall(self, edge_start, edge_end, z_base: float, floor_height: float, wall_offset: float = 0.05):
        """
        Render a wall as a vertical rectangle between two points.
        
        Args:
            edge_start: (x, y) start point of wall
            edge_end: (x, y) end point of wall
            z_base: Base Z height of the floor
            floor_height: Height of the floor
            wall_offset: Distance to offset wall inward (meters)
        """
        if not self.show_walls:
            return
        
        x1, y1 = edge_start
        x2, y2 = edge_end
        
        # Calculate inward normal (perpendicular to edge, pointing inward)
        dx = x2 - x1
        dy = y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        if length < 0.001:
            return  # Skip degenerate edges
        
        # Perpendicular vector (rotated 90 degrees counterclockwise)
        # This points to the left of the edge direction (inward for CCW polygons)
        normal_x = -dy / length
        normal_y = dx / length
        
        # Offset wall inward
        x1_offset = x1 + normal_x * wall_offset
        y1_offset = y1 + normal_y * wall_offset
        x2_offset = x2 + normal_x * wall_offset
        y2_offset = y2 + normal_y * wall_offset
        
        z_bottom = z_base
        z_top = z_base + floor_height
        
        # Use helper function to render
        self.render_vertical_rectangle(
            x1_offset, y1_offset, x2_offset, y2_offset,
            z_bottom, z_top,
            self.wall_color,
            outline_color=(0.4, 0.4, 0.35, 1.0),
            outline_width=1.0
        )
    
    def render_corner(self, corner, z_base: float, floor_height: float):
        """
        Render a corner as two flat rectangles on the wall surface at each corner vertex.
        
        Each corner gets two rectangles:
        - One extending from corner toward previous vertex
        - One extending from corner toward next vertex
        - Both span full floor height
        - Both are flat on the wall surface (like windows)
        
        Corners have a fixed small inset (like windows/doors), independent of wall_offset.
        
        Args:
            corner: Corner object with position and properties
            z_base: Base Z height of the floor
            floor_height: Height of the floor
        """
        if not self.show_corners:
            return
        
        position = corner.position
        prev_pos = corner.prev_position
        next_pos = corner.next_position
        corner_width = corner.width
        
        x, y = position
        z_bottom = z_base
        z_top = z_base + floor_height
        
        # Calculate direction to previous vertex (normalized)
        dx_prev = prev_pos[0] - x
        dy_prev = prev_pos[1] - y
        len_prev = (dx_prev * dx_prev + dy_prev * dy_prev) ** 0.5
        if len_prev < 0.001:
            return  # Skip degenerate edges
        dx_prev /= len_prev
        dy_prev /= len_prev
        
        # Calculate direction to next vertex (normalized)
        dx_next = next_pos[0] - x
        dy_next = next_pos[1] - y
        len_next = (dx_next * dx_next + dy_next * dy_next) ** 0.5
        if len_next < 0.001:
            return  # Skip degenerate edges
        dx_next /= len_next
        dy_next /= len_next
        
        # Calculate inward normal for each edge (90 degrees CCW)
        normal_prev_x = -dy_prev
        normal_prev_y = dx_prev
        normal_next_x = -dy_next
        normal_next_y = dx_next
        
        # Fixed small inset (like windows/doors) - independent of wall_offset
        corner_inset = 0.02  # 2cm inset from wall surface
        
        # Offset the corner vertex inward (use average normal)
        avg_normal_x = (normal_prev_x + normal_next_x)
        avg_normal_y = (normal_prev_y + normal_next_y)
        norm_len = (avg_normal_x * avg_normal_x + avg_normal_y * avg_normal_y) ** 0.5
        if norm_len > 0.001:
            avg_normal_x /= norm_len
            avg_normal_y /= norm_len
        
        corner_x = x + avg_normal_x * corner_inset
        corner_y = y + avg_normal_y * corner_inset
        
        # First rectangle: from corner toward previous vertex
        far_x = corner_x + dx_prev * corner_width
        far_y = corner_y + dy_prev * corner_width
        
        self.render_vertical_rectangle(
            corner_x, corner_y, far_x, far_y,
            z_bottom, z_top,
            self.corner_color
        )
        
        # Second rectangle: from corner toward next vertex
        far_x = corner_x + dx_next * corner_width
        far_y = corner_y + dy_next * corner_width
        
        self.render_vertical_rectangle(
            corner_x, corner_y, far_x, far_y,
            z_bottom, z_top,
            self.corner_color
        )
    
    def render_window(self, window, z_base: float):
        """
        Render a window as a vertical rectangle.
        
        Args:
            window: Window object with position and properties
            z_base: Base Z height of the floor
        """
        if not self.show_windows:
            return
        
        # Get window position
        pos = window.get_world_position()
        x, y = pos
        
        # Window dimensions
        width = window.width
        height = window.height
        elevation = window.elevation
        
        # Calculate window orientation (perpendicular to facing direction)
        facing_x, facing_y = window.facing_direction
        # Window width direction is perpendicular to facing
        width_x = -facing_y
        width_y = facing_x
        
        # Calculate window corners (slightly inset from wall for visibility)
        inset = 0.03  # 3cm inset from wall
        x_inset = x - facing_x * inset
        y_inset = y - facing_y * inset
        
        # Window endpoints
        hw = width / 2.0  # half width
        x1 = x_inset - width_x * hw
        y1 = y_inset - width_y * hw
        x2 = x_inset + width_x * hw
        y2 = y_inset + width_y * hw
        
        z_bottom = z_base + elevation
        z_top = z_bottom + height
        
        # Use helper function
        self.render_vertical_rectangle(
            x1, y1, x2, y2,
            z_bottom, z_top,
            self.window_color,
            outline_color=(0.3, 0.5, 0.6, 1.0),
            outline_width=1.5
        )
    
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
            
            # Get wall_offset from generation_params
            wall_offset = generation_params.get('wall_offset', 0.05) if generation_params else 0.05
            
            # Render walls for this floor
            if self.show_walls:
                edges = floor.footprint.get_edges()
                for edge_start, edge_end in edges:
                    self.render_wall(edge_start, edge_end, z_base, floor.height, wall_offset)
            
            # Render footprint outline (on top of walls)
            self.render_footprint(vertices, z_base, z_top)
            
            # Render corners for this floor
            if self.show_corners:
                corners = floor.get_corners(
                    seed=building.seed,
                    **generation_params
                )
                for corner in corners:
                    self.render_corner(corner, z_base, floor.height)
            
            # Render doors for this floor
            if self.show_doors:
                doors = floor.get_doors(
                    seed=building.seed,
                    **generation_params
                )
                for door in doors:
                    self.render_door(door, z_base)
            
            # Render windows for this floor
            if self.show_windows:
                windows = floor.get_windows(
                    seed=building.seed,
                    **generation_params
                )
                for window in windows:
                    self.render_window(window, z_base)
    
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
