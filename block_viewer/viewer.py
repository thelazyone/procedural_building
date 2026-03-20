"""
Standalone 3D viewer for blocks and subdivided building footprints.

Visualizes block outline and building footprints from subdivision.
"""

import sys
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.camera import OrbitCamera
from core.simple_ui import (
    Button,
    Label,
    TextInput,
    RadioButton,
    Checkbox,
    blur_text_inputs_unless_clicked,
    collect_text_inputs,
    wire_text_inputs_blur,
)
from block_viewer.renderer import BlockRenderer
from building_viewer.renderer import BuildingRenderer
from building import Building, generate_building_params
from utils.seeding import derive_seed
import random
from typing import List, Tuple

from blocks.subdivide import subdivide_block
from blocks.merge_fragments import merge_footprints_to_min_area
from blocks.filter_internal import filter_footprints_touching_block
from blocks.gap import apply_gaps
from blocks.facade_noise import apply_facade_noise
from blocks.facade_from_block import compute_facade_definition
from core.footprint_cleanup import prepare_footprint_for_adjacency
from blocks.stairs import collect_stairs_from_buildings


def _floor_counts_for_footprints(
    num_footprints: int,
    seed: int,
    avg_floors: float,
    variance: float,
) -> List[int]:
    """
    Compute floor count per footprint using normal distribution.

    variance=0: all buildings at avg_floors
    variance=1: spread such that buildings distributed ~uniformly in [0, 2*avg]
    sigma = variance * avg_floors; clamp to [0, 2*avg_floors]
    """
    if avg_floors <= 0:
        return [0] * num_footprints
    sigma = variance * avg_floors
    max_floors = max(0, int(2 * avg_floors))
    rng = random.Random(seed)
    counts = []
    for i in range(num_footprints):
        if sigma <= 0:
            count = avg_floors
        else:
            count = rng.gauss(avg_floors, sigma)
        count = max(0, min(max_floors, count))
        counts.append(int(count))  # floor: round down so zeros are possible
    return counts


def _building_seed(base_seed: int, building_idx: int, footprint: List[Tuple[float, float]]) -> int:
    """
    Derive a unique seed for a building from base seed and building identity.

    Each building gets a deterministic but unique seed by combining:
    - Base seed (passed through)
    - Building index (unique per footprint)
    - Footprint geometry hash (ensures different shapes get different seeds)

    Returns:
        Derived seed for this building's procedural generation
    """
    # Round vertices for stable hashing (avoid float precision issues)
    footprint_sig = tuple(tuple(round(c, 6) for c in v) for v in footprint)
    footprint_hash = hash(footprint_sig)
    return derive_seed(base_seed, "building", building_idx, footprint_hash)


class BlockViewer:
    """
    Main block viewer application.

    Provides UI for block selection and 3D visualization.
    """

    def __init__(self, width: int = 1600, height: int = 1000):
        self.width = width
        self.height = height
        self.ui_panel_width = 300
        self.viewport_x = self.ui_panel_width
        self.viewport_width = self.width - self.ui_panel_width

        pygame.init()
        self.screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Block Viewer")

        self.ui_surface = pygame.Surface((self.ui_panel_width, self.height))

        self.block_vertices = None
        self.footprint_vertices_list = []
        self._subdivide_cache_key = None
        self._user_cleared_block = False
        self.block_templates = self._create_templates()

        self.ui_elements = []
        self.radio_buttons = []
        self.text_inputs = []
        self.selected_block = None
        self._create_ui()

        self.camera = OrbitCamera(target=(0.0, 0.0, 3.0), distance=40.0)
        self.renderer = BlockRenderer()
        self.renderer.setup_gl(self.viewport_width, height)
        self.building_renderer = BuildingRenderer()
        self.building_renderer.setup_gl(self.viewport_width, height)

        self.clock = pygame.time.Clock()
        self.running = True

    def _create_templates(self):
        """Create predefined block footprint templates."""
        templates = {}

        # Square block (40x40)
        templates["Square Block"] = {
            "vertices": [
                (-20, -20), (20, -20), (20, 20), (-20, 20)
            ],
        }

        # Rectangle block (50x30)
        templates["Rectangle Block"] = {
            "vertices": [
                (-25, -15), (25, -15), (25, 15), (-25, 15)
            ],
        }

        # L-shaped block
        templates["L-Shaped Block"] = {
            "vertices": [
                (-20, -20), (20, -20), (20, 0), (0, 0), (0, 20), (-20, 20)
            ],
        }

        # Irregular / trapezoid
        templates["Trapezoid Block"] = {
            "vertices": [
                (-25, -15), (25, -15), (15, 15), (-15, 15)
            ],
        }

        # Larger square block
        templates["Large Square"] = {
            "vertices": [
                (-30, -30), (30, -30), (30, 30), (-30, 30)
            ],
        }

        return templates

    def _create_ui(self):
        """Create UI elements."""
        y = 20

        self.ui_elements.append(Label((10, y), "Blocks:", 24))
        y += 35

        block_names = list(self.block_templates.keys())
        for i, name in enumerate(block_names):
            radio = RadioButton(
                pygame.Rect(10, y, 280, 30),
                name,
                lambda n=name: self._load_block(n),
                selected=(i == 0),
            )
            self.radio_buttons.append(radio)
            self.ui_elements.append(radio)
            y += 35

        y += 10
        clear_btn = Button(pygame.Rect(10, y, 280, 35), "Clear", self._clear_block)
        self.ui_elements.append(clear_btn)
        y += 50

        self.ui_elements.append(Label((10, y), "Parameters:", 22))
        y += 30

        self.ui_elements.append(Label((10, y + 5), "Seed:", 20))
        self.seed_input = TextInput(pygame.Rect(72, y, 118, 30), "12345")
        self.ui_elements.append(self.seed_input)
        rnd_seed_btn = Button(
            pygame.Rect(195, y, 95, 30),
            "Random",
            self._random_block_seed,
        )
        self.ui_elements.append(rnd_seed_btn)
        y += 35

        self.ui_elements.append(Label((10, y + 5), "Min Area:", 20))
        self.min_area_input = TextInput(pygame.Rect(100, y, 190, 30), "50")
        self.ui_elements.append(self.min_area_input)
        y += 35

        self.ui_elements.append(Label((10, y + 5), "Fragmentation:", 20))
        self.fragmentation_input = TextInput(pygame.Rect(100, y, 190, 30), "2")
        self.ui_elements.append(self.fragmentation_input)
        self.text_inputs.append(self.fragmentation_input)
        y += 35

        self.ui_elements.append(Label((10, y + 5), "Avg floors:", 20))
        self.avg_floors_input = TextInput(pygame.Rect(100, y, 190, 30), "5")
        self.ui_elements.append(self.avg_floors_input)
        y += 35

        self.ui_elements.append(Label((10, y + 5), "Variance:", 20))
        self.variance_input = TextInput(pygame.Rect(100, y, 190, 30), "0.5")
        self.ui_elements.append(self.variance_input)
        self.text_inputs.append(self.variance_input)
        y += 35

        self.ui_elements.append(Label((10, y + 5), "Gap chance:", 20))
        self.gap_chance_input = TextInput(pygame.Rect(100, y, 190, 30), "0.2")
        self.ui_elements.append(self.gap_chance_input)
        y += 35

        self.ui_elements.append(Label((10, y + 5), "Gap size:", 20))
        self.gap_size_input = TextInput(pygame.Rect(100, y, 190, 30), "2")
        self.ui_elements.append(self.gap_size_input)
        self.text_inputs.append(self.gap_size_input)
        y += 35

        self.ui_elements.append(Label((10, y + 5), "Facade noise:", 20))
        self.facade_noise_input = TextInput(pygame.Rect(100, y, 190, 30), "0")
        self.ui_elements.append(self.facade_noise_input)
        y += 35

        reload_btn = Button(pygame.Rect(10, y, 280, 35), "Reload", self._reload_block)
        self.ui_elements.append(reload_btn)
        y += 50

        self.ui_elements.append(Label((10, y), "Visibility:", 22))
        y += 30

        self.block_outline_cb = Checkbox(
            pygame.Rect(10, y, 280, 30), "Block outline", True
        )
        self.ui_elements.append(self.block_outline_cb)
        y += 35

        self.footprints_cb = Checkbox(
            pygame.Rect(10, y, 280, 30), "Building footprints", True
        )
        self.ui_elements.append(self.footprints_cb)
        y += 35

        self.remove_internal_cb = Checkbox(
            pygame.Rect(10, y, 280, 30), "Remove internal", True
        )
        self.ui_elements.append(self.remove_internal_cb)
        y += 35

        self.show_3d_cb = Checkbox(
            pygame.Rect(10, y, 280, 30), "Show 3D buildings", True
        )
        self.ui_elements.append(self.show_3d_cb)
        y += 35

        self.full_details_cb = Checkbox(
            pygame.Rect(10, y, 280, 30), "Full building details", False
        )
        self.ui_elements.append(self.full_details_cb)
        y += 35

        self.show_roof_cb = Checkbox(
            pygame.Rect(10, y, 280, 30), "Show roof", True
        )
        self.ui_elements.append(self.show_roof_cb)
        y += 35

        self.grid_cb = Checkbox(pygame.Rect(10, y, 280, 30), "Grid", True)
        self.ui_elements.append(self.grid_cb)
        y += 50

        self.ui_elements.append(Label((10, y), "Facade edges:", 22))
        y += 28
        self.ui_elements.append(
            Label((10, y), "Ground always; upper floors if 3D on", 14)
        )
        y += 22
        self.ui_elements.append(Label((10, y), "Blue=front, Orange=occlusion, Gray=back", 14))

        wire_text_inputs_blur(self.ui_elements, self._commit_block_params)
        self.text_inputs = collect_text_inputs(self.ui_elements)

        self.selected_block = block_names[0]
        self._load_block(block_names[0])

    @staticmethod
    def _fmt_num(v: float) -> str:
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return str(v)

    def _normalize_block_panel_fields(self) -> None:
        """Clamp invalid / empty text to defaults (call on blur / commit only)."""
        s = self.seed_input.text.strip()
        if not s:
            self.seed_input.text = "12345"
        else:
            try:
                self.seed_input.text = str(int(s))
            except ValueError:
                self.seed_input.text = "12345"

        s = self.min_area_input.text.strip()
        try:
            v = float(s) if s else 50.0
            self.min_area_input.text = self._fmt_num(max(v, 0.01))
        except ValueError:
            self.min_area_input.text = "50"

        s = self.fragmentation_input.text.strip()
        try:
            v = float(s) if s else 2.0
            v = max(1.0, v)
            self.fragmentation_input.text = self._fmt_num(v)
        except ValueError:
            self.fragmentation_input.text = "2"

        for inp, default in (
            (self.avg_floors_input, 5.0),
            (self.variance_input, 0.5),
            (self.gap_chance_input, 0.2),
            (self.gap_size_input, 2.0),
            (self.facade_noise_input, 0.0),
        ):
            s = inp.text.strip()
            try:
                v = float(s) if s else default
                inp.text = self._fmt_num(v)
            except ValueError:
                inp.text = self._fmt_num(default)

        try:
            gc = float(self.gap_chance_input.text)
            gc = max(0.0, min(1.0, gc))
            self.gap_chance_input.text = self._fmt_num(gc)
        except ValueError:
            self.gap_chance_input.text = "0.2"

        try:
            vv = float(self.variance_input.text)
            vv = max(0.0, min(1.0, vv))
            self.variance_input.text = self._fmt_num(vv)
        except ValueError:
            self.variance_input.text = "0.5"

    def _commit_block_params(self) -> None:
        """Apply panel values: normalize text, then subdivide if needed (blur / leave field)."""
        self._sync_block_subdivision(force=False, commit=True)

    def _random_block_seed(self) -> None:
        self.seed_input.text = str(random.randint(0, 2**31 - 1))
        self.seed_input.active = False
        self.seed_input._replace_next = False
        self._sync_block_subdivision(force=False, commit=True)

    def _sync_block_subdivision(self, force: bool = False, commit: bool = False) -> None:
        """
        Recompute building lots from the current template + seed + min area + fragmentation.

        Call with commit=True after editing (blur) to normalize fields and subdivide.
        force=True skips cache (new block template or Reload).
        """
        if getattr(self, "_user_cleared_block", False):
            return
        if not self.selected_block or self.selected_block not in self.block_templates:
            return

        template = self.block_templates[self.selected_block]
        block_vertices = template["vertices"]

        if commit or force:
            self._normalize_block_panel_fields()

        seed = int(self.seed_input.text)
        min_area = float(self.min_area_input.text)
        fragmentation = max(1.0, float(self.fragmentation_input.text))

        key = (self.selected_block, seed, min_area, fragmentation)
        if not force and key == getattr(self, "_subdivide_cache_key", None):
            self.block_vertices = block_vertices
            return

        fragments = subdivide_block(
            block_vertices,
            seed=seed,
            min_area=min_area,
            chance_no_divide=0.05,
            fragmentation=fragmentation,
        )
        merge_seed = derive_seed(seed, "merge_footprints", self.selected_block)
        self.footprint_vertices_list = merge_footprints_to_min_area(
            fragments,
            block_vertices,
            min_area=min_area,
            seed=merge_seed,
        )
        self._subdivide_cache_key = key
        self.block_vertices = block_vertices
        print(
            f"Subdivided {self.selected_block} seed={seed} min_area={min_area} "
            f"frag={fragmentation} -> {len(fragments)} frags -> "
            f"{len(self.footprint_vertices_list)} lots"
        )

    def _load_block(self, block_name: str):
        """Select block template and subdivide."""
        if block_name not in self.block_templates:
            return

        self.selected_block = block_name
        self._user_cleared_block = False
        for radio in self.radio_buttons:
            radio.selected = (radio.text == block_name)

        self._sync_block_subdivision(force=True, commit=True)

    def _reload_block(self):
        """Force subdivision with current seed / min area (same as re-selecting block)."""
        if self.selected_block:
            self._sync_block_subdivision(force=True, commit=True)

    def _clear_block(self):
        """Clear current block."""
        self.block_vertices = None
        self.footprint_vertices_list = []
        self._subdivide_cache_key = None
        self._user_cleared_block = True
        print("Block cleared")

    def _handle_events(self):
        """Handle pygame events."""
        self.clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                blur_text_inputs_unless_clicked(self.text_inputs, event)

            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < self.ui_panel_width:
                for element in self.ui_elements:
                    if hasattr(element, "handle_event"):
                        element.handle_event(event)

                self.renderer.show_block_outline = self.block_outline_cb.checked
                self.renderer.show_footprints = self.footprints_cb.checked
                self.renderer.show_grid = self.grid_cb.checked
                self.building_renderer.show_roof = self.show_roof_cb.checked
            else:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.camera.handle_mouse_down(mouse_pos, event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.camera.handle_mouse_up(mouse_pos, event.button)
                elif event.type == pygame.MOUSEMOTION:
                    self.camera.handle_mouse_motion(mouse_pos)
                elif event.type == pygame.MOUSEWHEEL:
                    self.camera.handle_mouse_wheel(event.y)

    def _render(self):
        """Render frame."""
        glClearColor(0.15, 0.15, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(self.viewport_x, 0, self.viewport_width, self.height)
        glScissor(self.viewport_x, 0, self.viewport_width, self.height)
        glEnable(GL_SCISSOR_TEST)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        from OpenGL.GLU import gluPerspective
        gluPerspective(45, self.viewport_width / self.height, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.camera.apply()

        glEnable(GL_DEPTH_TEST)
        self.renderer.render_grid()

        if self.block_vertices is not None and self.footprint_vertices_list is not None:
            footprints = self.footprint_vertices_list
            if self.remove_internal_cb.checked:
                footprints = filter_footprints_touching_block(
                    self.block_vertices, footprints
                )
            try:
                gap_chance = float(self.gap_chance_input.text)
            except (ValueError, AttributeError):
                gap_chance = 0.2
            try:
                gap_size = float(self.gap_size_input.text)
            except (ValueError, AttributeError):
                gap_size = 2.0
            try:
                seed = int(self.seed_input.text)
            except (ValueError, AttributeError):
                seed = 12345
            footprints = apply_gaps(
                footprints,
                seed=seed,
                gap_chance=max(0, min(1, gap_chance)),
                gap_size=max(0, gap_size),
                block_vertices=self.block_vertices,
            )
            try:
                facade_noise = float(self.facade_noise_input.text)
            except (ValueError, AttributeError):
                facade_noise = 0.0
            facade_noise = max(0.0, facade_noise)
            footprints = apply_facade_noise(
                footprints,
                seed=seed,
                facade_noise=facade_noise,
                block_vertices=self.block_vertices,
            )
            # Dedupe collinear vertices before facade adjacency (front/back/occlusion)
            footprints = [
                prepare_footprint_for_adjacency(fp) for fp in footprints
            ]
            footprints = [fp for fp in footprints if len(fp) >= 3]
            # floor_height is per-building from params (generate_building_params)
            try:
                avg_floors = float(self.avg_floors_input.text)
            except (ValueError, AttributeError):
                avg_floors = 5.0
            try:
                variance = float(self.variance_input.text)
            except (ValueError, AttributeError):
                variance = 0.5
            variance = max(0.0, min(1.0, variance))
            try:
                seed = int(self.seed_input.text)
            except (ValueError, AttributeError):
                seed = 12345
            floor_counts = _floor_counts_for_footprints(
                len(footprints), seed, avg_floors, variance
            )

            use_full_details = (
                self.full_details_cb.checked and self.show_3d_cb.checked
            )
            buildings_visible = self.footprints_cb.checked

            # Pre-generate building params for ALL buildings first (deterministic metadata)
            # This gives per-building floor_height for cubes, facade, occlusion_height
            # building_heights includes roof (affects occlusion, stairs)
            building_params_list = []
            building_floor_heights = []
            building_roof_heights = []
            building_heights = []
            for i, footprint in enumerate(footprints):
                num_floors = floor_counts[i] if i < len(floor_counts) else 0
                if num_floors > 0:
                    building_seed = _building_seed(seed, i, footprint)
                    params = generate_building_params(building_seed)
                    building_params_list.append(params)
                    fh = params.get("floor_height", 3.0)
                    roof_h = params.get("roof_height", 0.5)
                    building_floor_heights.append(fh)
                    building_roof_heights.append(roof_h)
                    building_heights.append(num_floors * fh + roof_h)
                else:
                    building_params_list.append(None)
                    building_floor_heights.append(0.0)
                    building_roof_heights.append(0.0)
                    building_heights.append(0.0)

            # Compute facade definitions (with occlusion_height from adjacent buildings)
            facade_definitions = []
            for i, fp in enumerate(footprints):
                fd = compute_facade_definition(
                    fp, i, footprints,
                    block_vertices=self.block_vertices,
                    building_heights=building_heights,
                )
                facade_definitions.append(fd)

            if use_full_details and buildings_visible:
                # Generate individual buildings with full details (doors, windows, etc.)
                # Params already generated above
                self.renderer.render_block_outline(self.block_vertices)
                courtyard_color = (0.35, 0.4, 0.35, 0.5)
                z_base = 0.01
                buildings_list = [None] * len(footprints)
                for i, footprint in enumerate(footprints):
                    num_floors = floor_counts[i] if i < len(floor_counts) else 0
                    if num_floors > 0:
                        building_seed = _building_seed(seed, i, footprint)
                        params = dict(building_params_list[i])  # copy, we may pop
                        floors_data = [footprint] * num_floors
                        building_floor_height = params.pop("floor_height", 3.0)
                        floor_heights = [building_floor_height] * num_floors
                        building = Building(
                            floors=floors_data,
                            seed=building_seed,
                            floor_heights=floor_heights,
                            facade_definition=facade_definitions[i],
                            **params,
                        )
                        buildings_list[i] = building
                        self.building_renderer.render_building(
                            building, params
                        )
                    elif buildings_visible:
                        self.renderer.render_footprint_flat(
                            footprint, courtyard_color, z_base
                        )
                # Block-level stairs: doors above occlusion
                stairs = collect_stairs_from_buildings(
                    buildings_list,
                    footprints,
                    facade_definitions,
                    building_heights,
                    building_params_list=building_params_list,
                )
                self.renderer.render_stairs(stairs)

            # Render facade segment colors
            if buildings_visible:
                for i, footprint in enumerate(footprints):
                    if i >= len(facade_definitions):
                        continue
                    num_floors = floor_counts[i] if i < len(floor_counts) else 0
                    if use_full_details and num_floors > 0:
                        # Full details: ground-level only
                        self.renderer.render_footprint_facade_segments(
                            footprint, facade_definitions[i], z=0.02
                        )
                    elif not use_full_details and num_floors > 0:
                        # Ground floor always; upper floors only when extruded 3D is shown
                        fh = building_floor_heights[i] if i < len(building_floor_heights) else 3.0
                        max_floor = (
                            num_floors if self.show_3d_cb.checked else 1
                        )
                        for floor_idx in range(max_floor):
                            fz_base = floor_idx * fh
                            fz_top = (floor_idx + 1) * fh
                            z_line = fz_base + 0.01
                            self.renderer.render_footprint_facade_segments(
                                footprint,
                                facade_definitions[i],
                                z=z_line,
                                floor_z_base=fz_base,
                                floor_z_top=fz_top,
                            )
                    else:
                        # Courtyards: ground-level only
                        self.renderer.render_footprint_facade_segments(
                            footprint, facade_definitions[i], z=0.02
                        )

            if not use_full_details and buildings_visible:
                self.renderer.render_block(
                    self.block_vertices,
                    footprints,
                    show_3d=self.show_3d_cb.checked,
                    floor_height=3.0,  # Fallback only; per-building from building_floor_heights
                    floor_counts=floor_counts,
                    floor_heights=building_floor_heights,
                    roof_heights=building_roof_heights,
                )
            else:
                # Buildings hidden - still show block outline
                self.renderer.render_block_outline(self.block_vertices)

        glDisable(GL_SCISSOR_TEST)

        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        self.ui_surface.fill((40, 40, 40))
        for element in self.ui_elements:
            element.draw(self.ui_surface)

        ui_string = pygame.image.tostring(self.ui_surface, "RGBA", True)
        glRasterPos2i(0, 0)
        glDrawPixels(
            self.ui_panel_width, self.height, GL_RGBA, GL_UNSIGNED_BYTE, ui_string
        )

        pygame.display.flip()

    def run(self):
        """Main application loop."""
        print("=== Block Viewer ===")
        print("Controls:")
        print("  - Left mouse drag: Rotate camera")
        print("  - Middle mouse drag: Pan view")
        print("  - Mouse wheel: Zoom in/out")
        print("  - Tab/Enter/click away commits; Random picks a new seed")
        print("  - Reload forces re-subdivide with current values")
        print()

        while self.running:
            self._handle_events()
            self._render()

        pygame.quit()


def main():
    """Entry point for block viewer."""
    viewer = BlockViewer()
    viewer.run()


if __name__ == "__main__":
    main()
