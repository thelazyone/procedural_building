"""
3D renderer for block and footprint visualization.

Renders block outline and subdivided building footprints.
Footprints are convex (concave ones split in pipeline). Triangle fan for fill.
"""

from typing import List, Tuple
from OpenGL.GL import *
from OpenGL.GLU import *

from core.footprint import Point2D


def _triangulate_polygon(vertices: List[Point2D]) -> List[Tuple[Point2D, Point2D, Point2D]]:
    """Triangulate a convex polygon using a triangle fan."""
    n = len(vertices)
    if n < 3:
        return []
    if n == 3:
        return [(vertices[0], vertices[1], vertices[2])]
    triangles = []
    v0 = vertices[0]
    for i in range(1, n - 1):
        triangles.append((v0, vertices[i], vertices[i + 1]))
    return triangles


# Distinct colors for building footprints (flat for now)
FOOTPRINT_COLORS = [
    (0.4, 0.6, 0.9, 0.7),   # Blue
    (0.6, 0.8, 0.5, 0.7),   # Green
    (0.9, 0.6, 0.4, 0.7),   # Orange
    (0.8, 0.5, 0.8, 0.7),   # Purple
    (0.5, 0.8, 0.8, 0.7),   # Cyan
    (0.9, 0.8, 0.4, 0.7),   # Yellow
    (0.7, 0.5, 0.6, 0.7),   # Mauve
    (0.5, 0.7, 0.6, 0.7),   # Teal
]


class BlockRenderer:
    """
    Renders block outline and building footprints in 3D.

    Block: single outline (e.g. gray).
    Footprints: flat polygons for now; later extruded by floor count.
    """

    def __init__(self):
        """Initialize renderer."""
        self.show_block_outline = True
        self.show_footprints = True
        self.show_grid = True

        self.block_outline_color = (0.5, 0.5, 0.5, 1.0)
        self.grid_color = (0.3, 0.3, 0.3, 1.0)

    def setup_gl(self, width: int, height: int):
        """Setup OpenGL state."""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.15, 0.15, 0.15, 1.0)

    def render_grid(self, size: float = 80.0, step: float = 5.0):
        """Render ground grid."""
        if not self.show_grid:
            return
        glColor4f(*self.grid_color)
        glBegin(GL_LINES)
        half_size = size / 2
        num_lines = int(size / step) + 1
        for i in range(num_lines):
            offset = -half_size + i * step
            glVertex3f(-half_size, offset, 0)
            glVertex3f(half_size, offset, 0)
            glVertex3f(offset, -half_size, 0)
            glVertex3f(offset, half_size, 0)
        glEnd()

    def render_block_outline(self, vertices: List[Point2D], z: float = 0.0):
        """Render block boundary as outline only."""
        if not self.show_block_outline or not vertices:
            return
        glLineWidth(3.0)
        glColor4f(*self.block_outline_color)
        glBegin(GL_LINE_LOOP)
        for x, y in vertices:
            glVertex3f(x, y, z)
        glEnd()
        glLineWidth(1.0)

    def render_footprint_flat(
        self,
        vertices: List[Point2D],
        color: Tuple[float, float, float, float],
        z: float = 0.01,  # Slightly above grid to avoid z-fighting
    ):
        """Render a single footprint as flat polygon."""
        if not self.show_footprints or not vertices:
            return
        glColor4f(*color)
        for v0, v1, v2 in _triangulate_polygon(vertices):
            glBegin(GL_TRIANGLES)
            glVertex3f(v0[0], v0[1], z)
            glVertex3f(v1[0], v1[1], z)
            glVertex3f(v2[0], v2[1], z)
            glEnd()
        glLineWidth(1.5)
        glColor4f(
            color[0] * 0.7, color[1] * 0.7, color[2] * 0.7, 1.0
        )
        glBegin(GL_LINE_LOOP)
        for x, y in vertices:
            glVertex3f(x, y, z)
        glEnd()
        glLineWidth(1.0)

    def render_footprint_extruded(
        self,
        vertices: List[Point2D],
        color: Tuple[float, float, float, float],
        z_base: float,
        height: float,
    ):
        """Render a footprint as extruded 3D volume."""
        if not self.show_footprints or not vertices or height <= 0:
            return
        z_top = z_base + height
        n = len(vertices)

        top_color = (
            min(1.0, color[0] * 1.2),
            min(1.0, color[1] * 1.2),
            min(1.0, color[2] * 1.2),
            color[3],
        )
        glColor4f(*top_color)
        for v0, v1, v2 in _triangulate_polygon(vertices):
            glBegin(GL_TRIANGLES)
            glVertex3f(v0[0], v0[1], z_top)
            glVertex3f(v1[0], v1[1], z_top)
            glVertex3f(v2[0], v2[1], z_top)
            glEnd()

        glColor4f(*color)
        rev = list(reversed(vertices))
        for v0, v1, v2 in _triangulate_polygon(rev):
            glBegin(GL_TRIANGLES)
            glVertex3f(v0[0], v0[1], z_base)
            glVertex3f(v1[0], v1[1], z_base)
            glVertex3f(v2[0], v2[1], z_base)
            glEnd()

        edge_color = (
            color[0] * 0.85, color[1] * 0.85, color[2] * 0.85, color[3]
        )
        glColor4f(*edge_color)
        for i in range(n):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % n]
            glBegin(GL_QUADS)
            glVertex3f(x1, y1, z_base)
            glVertex3f(x2, y2, z_base)
            glVertex3f(x2, y2, z_top)
            glVertex3f(x1, y1, z_top)
            glEnd()

        glLineWidth(1.5)
        glColor4f(edge_color[0] * 0.7, edge_color[1] * 0.7, edge_color[2] * 0.7, 1.0)
        glBegin(GL_LINE_LOOP)
        for x, y in vertices:
            glVertex3f(x, y, z_top)
        glEnd()
        glLineWidth(1.0)

    def render_block(
        self,
        block_vertices: List[Point2D],
        footprint_vertices_list: List[List[Point2D]],
        show_3d: bool = True,
        floor_height: float = 3.0,
        floor_counts: List[int] = None,
    ):
        """
        Render block and all subdivided footprints.

        Args:
            block_vertices: Block boundary
            footprint_vertices_list: List of building footprint vertex lists
            show_3d: If True, extrude footprints; if False, render flat
            floor_height: Height per floor in meters
            floor_counts: Floor count per footprint (0 = no building, courtyard)
        """
        # Block outline
        self.render_block_outline(block_vertices)

        z_base = 0.01  # Slightly above grid
        if floor_counts is None:
            floor_counts = [2] * len(footprint_vertices_list)

        for i, footprint in enumerate(footprint_vertices_list):
            color = FOOTPRINT_COLORS[i % len(FOOTPRINT_COLORS)]
            num_floors = floor_counts[i] if i < len(floor_counts) else 0
            if show_3d and num_floors > 0:
                building_height = floor_height * num_floors
                self.render_footprint_extruded(
                    footprint, color, z_base, building_height
                )
            elif show_3d and num_floors == 0:
                # Zero floors = courtyard/empty lot, render flat with muted color
                courtyard_color = (0.35, 0.4, 0.35, 0.5)
                self.render_footprint_flat(footprint, courtyard_color, z_base)
            else:
                self.render_footprint_flat(footprint, color, z_base)
