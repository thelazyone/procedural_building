"""
3D renderer for block and footprint visualization.

Renders block outline and subdivided building footprints.
Footprints are convex (concave ones split in pipeline). Triangle fan for fill.
"""

from typing import List, Tuple, Optional
from OpenGL.GL import *
from OpenGL.GLU import *

from core.footprint import Point2D
from core.facade import FacadeDefinition, FacadeSegmentKind

# Stair rendering
STAIR_COLOR = (0.5, 0.45, 0.4, 0.9)  # Wood/concrete ramp
STAIR_RAMP_WIDTH = 1.2  # meters, door-like width


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


# Consistent colors for facade segment kinds (same across all buildings)
FACADE_FRONT_COLOR = (0.2, 0.6, 0.9, 1.0)      # Blue - main road face
FACADE_OCCLUSION_COLOR = (0.9, 0.5, 0.2, 1.0)  # Orange - facing other buildings
FACADE_BACK_COLOR = (0.4, 0.5, 0.45, 1.0)     # Gray-green - backroad sides

FACADE_KIND_COLORS = {
    FacadeSegmentKind.FRONT: FACADE_FRONT_COLOR,
    FacadeSegmentKind.OCCLUSION: FACADE_OCCLUSION_COLOR,
    FacadeSegmentKind.BACK: FACADE_BACK_COLOR,
}

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

    def render_footprint_facade_segments(
        self,
        vertices: List[Point2D],
        facade_definition: FacadeDefinition,
        z: float = 0.01,
        line_width: float = 4.0,
        floor_z_base: Optional[float] = None,
        floor_z_top: Optional[float] = None,
    ):
        """
        Render footprint edges with colors by facade segment kind at z plane.

        FRONT=blue, OCCLUSION=orange, BACK=gray-green. Same colors for all buildings.

        When floor_z_base and floor_z_top are provided, uses effective kind for that
        floor (OCCLUSION segments above occlusion_height render as BACK).
        """
        if not self.show_footprints or not vertices or not facade_definition.segments:
            return

        n = len(vertices)
        edges = [
            (vertices[i], vertices[(i + 1) % n])
            for i in range(n)
        ]

        use_effective = (
            floor_z_base is not None and floor_z_top is not None
        )

        glLineWidth(line_width)
        for seg in facade_definition.segments:
            if seg.edge_idx >= len(edges):
                continue
            start_pt, end_pt = edges[seg.edge_idx]
            sx, sy = start_pt
            ex, ey = end_pt
            # Parametric interpolation
            x1 = sx + seg.start_param * (ex - sx)
            y1 = sy + seg.start_param * (ey - sy)
            x2 = sx + seg.end_param * (ex - sx)
            y2 = sy + seg.end_param * (ey - sy)
            kind = (
                seg.effective_kind_at_height(floor_z_base, floor_z_top)
                if use_effective
                else seg.kind
            )
            color = FACADE_KIND_COLORS.get(kind, FACADE_BACK_COLOR)
            glColor4f(*color)
            glBegin(GL_LINES)
            glVertex3f(x1, y1, z)
            glVertex3f(x2, y2, z)
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

        # Top face (colored - grey roof only in full-details mode via BuildingRenderer)
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
        glColor4f(
            top_color[0] * 0.7, top_color[1] * 0.7, top_color[2] * 0.7, 1.0
        )
        glBegin(GL_LINE_LOOP)
        for x, y in vertices:
            glVertex3f(x, y, z_top)
        glEnd()
        glLineWidth(1.0)

    def render_stair(self, stair, ramp_width: float = STAIR_RAMP_WIDTH):
        """
        Render a single stair. Two variants:
        - ramp: Simple 45° ramp in door direction.
        - landing_side_ramp: Horizontal square landing + side ramp (when drop > 1m).
        """
        x, y = stair.from_position
        from_z = stair.from_z
        to_z = stair.to_z
        drop = from_z - to_z
        if drop <= 0:
            return

        dx, dy = stair.direction
        wx = -dy * (ramp_width / 2)
        wy = dx * (ramp_width / 2)

        if stair.variant == "landing_side_ramp" and stair.side_ramp_direction:
            # Landing: horizontal square in front of door
            sdx, sdy = stair.side_ramp_direction
            # Back edge at door, front edge at door + direction * ramp_width
            back_left = (x - dy * ramp_width / 2, y + dx * ramp_width / 2, from_z)
            back_right = (x + dy * ramp_width / 2, y - dx * ramp_width / 2, from_z)
            front_right = (x + dx * ramp_width + dy * ramp_width / 2,
                           y + dy * ramp_width - dx * ramp_width / 2, from_z)
            front_left = (x + dx * ramp_width - dy * ramp_width / 2,
                          y + dy * ramp_width + dx * ramp_width / 2, from_z)
            glColor4f(*STAIR_COLOR)
            glBegin(GL_QUADS)
            glVertex3f(*back_left)
            glVertex3f(*back_right)
            glVertex3f(*front_right)
            glVertex3f(*front_left)
            glEnd()
            # Side ramp: from landing edge in +side_ramp_direction, extends outward
            h = drop  # 45° ramp horizontal distance
            # Ramp attaches to landing edge in +side_ramp_direction (the "front" edge)
            landing_center = (x + dx * ramp_width / 2, y + dy * ramp_width / 2)
            near_cx = landing_center[0] + sdx * ramp_width / 2
            near_cy = landing_center[1] + sdy * ramp_width / 2
            # Ramp quad: near edge perpendicular to side_ramp_direction
            perp_x, perp_y = -sdy, sdx
            ramp_near_left = (near_cx - perp_x * ramp_width / 2, near_cy - perp_y * ramp_width / 2, from_z)
            ramp_near_right = (near_cx + perp_x * ramp_width / 2, near_cy + perp_y * ramp_width / 2, from_z)
            ramp_far_left = (near_cx - perp_x * ramp_width / 2 + sdx * h,
                             near_cy - perp_y * ramp_width / 2 + sdy * h, to_z)
            ramp_far_right = (near_cx + perp_x * ramp_width / 2 + sdx * h,
                              near_cy + perp_y * ramp_width / 2 + sdy * h, to_z)
            glBegin(GL_QUADS)
            glVertex3f(*ramp_near_left)
            glVertex3f(*ramp_near_right)
            glVertex3f(*ramp_far_right)
            glVertex3f(*ramp_far_left)
            glEnd()
            glColor4f(0.35, 0.32, 0.28, 1.0)
            glLineWidth(1.5)
            glBegin(GL_LINE_LOOP)
            glVertex3f(*back_left)
            glVertex3f(*back_right)
            glVertex3f(*front_right)
            glVertex3f(*front_left)
            glEnd()
            glBegin(GL_LINE_LOOP)
            glVertex3f(*ramp_near_left)
            glVertex3f(*ramp_near_right)
            glVertex3f(*ramp_far_right)
            glVertex3f(*ramp_far_left)
            glEnd()
            glLineWidth(1.0)
        else:
            # Simple ramp
            h = drop
            lx = x + dx * h
            ly = y + dy * h
            p1 = (x + wx, y + wy, from_z)
            p2 = (x - wx, y - wy, from_z)
            p3 = (lx - wx, ly - wy, to_z)
            p4 = (lx + wx, ly + wy, to_z)
            glColor4f(*STAIR_COLOR)
            glBegin(GL_QUADS)
            glVertex3f(*p1)
            glVertex3f(*p2)
            glVertex3f(*p3)
            glVertex3f(*p4)
            glEnd()
            glColor4f(0.35, 0.32, 0.28, 1.0)
            glLineWidth(1.5)
            glBegin(GL_LINE_LOOP)
            glVertex3f(*p1)
            glVertex3f(*p2)
            glVertex3f(*p3)
            glVertex3f(*p4)
            glEnd()
            glLineWidth(1.0)

    def render_stairs(self, stairs: list, ramp_width: float = STAIR_RAMP_WIDTH):
        """Render a list of stairs as simple ramps."""
        for stair in stairs:
            self.render_stair(stair, ramp_width)

    def render_block(
        self,
        block_vertices: List[Point2D],
        footprint_vertices_list: List[List[Point2D]],
        show_3d: bool = True,
        floor_height: float = 3.0,
        floor_counts: List[int] = None,
        floor_heights: Optional[List[float]] = None,
        roof_heights: Optional[List[float]] = None,
    ):
        """
        Render block and all subdivided footprints.

        Args:
            block_vertices: Block boundary
            footprint_vertices_list: List of building footprint vertex lists
            show_3d: If True, extrude footprints; if False, render flat
            floor_height: Default height per floor (used when floor_heights not provided)
            floor_counts: Floor count per footprint (0 = no building, courtyard)
            floor_heights: Per-building floor height in meters. When provided,
                each building uses its own floor height for extrusion.
            roof_heights: Per-building roof height in meters. Added to total height.
        """
        # Block outline
        self.render_block_outline(block_vertices)

        z_base = 0.01  # Slightly above grid
        if floor_counts is None:
            floor_counts = [2] * len(footprint_vertices_list)

        for i, footprint in enumerate(footprint_vertices_list):
            color = FOOTPRINT_COLORS[i % len(FOOTPRINT_COLORS)]
            num_floors = floor_counts[i] if i < len(floor_counts) else 0
            fh = (
                floor_heights[i]
                if floor_heights and i < len(floor_heights)
                else floor_height
            )
            roof_h = (
                roof_heights[i]
                if roof_heights and i < len(roof_heights)
                else 0.5
            )
            if show_3d and num_floors > 0:
                building_height = fh * num_floors + roof_h
                self.render_footprint_extruded(
                    footprint, color, z_base, building_height
                )
            elif show_3d and num_floors == 0:
                # Zero floors = courtyard/empty lot, render flat with muted color
                courtyard_color = (0.35, 0.4, 0.35, 0.5)
                self.render_footprint_flat(footprint, courtyard_color, z_base)
            else:
                self.render_footprint_flat(footprint, color, z_base)
