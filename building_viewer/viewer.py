"""
Standalone 3D viewer for individual procedural buildings.

This is a separate application that imports the procedural_building library
and provides real-time visualization and parameter adjustment.
"""

import sys
import os
import random
import pygame
from pygame.locals import *
from OpenGL.GL import *

# Add parent directory to path to import procedural_building
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from building import Building
from core.camera import OrbitCamera
from core.simple_ui import (
    Button,
    Label,
    TextInput,
    Checkbox,
    RadioButton,
    blur_text_inputs_unless_clicked,
    collect_text_inputs,
    wire_text_inputs_blur,
)
from building_viewer.renderer import BuildingRenderer


class BuildingViewer:
    """
    Main building viewer application.

    Provides UI for building selection and 3D visualization.
    """

    def __init__(self, width: int = 1600, height: int = 1000):
        """
        Initialize building viewer.

        Args:
            width: Window width in pixels
            height: Window height in pixels
        """
        self.width = width
        self.height = height
        self.ui_panel_width = 300
        self.viewport_x = self.ui_panel_width
        self.viewport_width = self.width - self.ui_panel_width

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (width, height),
            DOUBLEBUF | OPENGL
        )
        pygame.display.set_caption("Building Viewer")

        # Create UI surface (for rendering UI separately)
        self.ui_surface = pygame.Surface((self.ui_panel_width, self.height))

        # Building data (create templates first, before UI)
        self.current_building = None
        self.building_templates = self.create_building_templates()

        # Create UI elements
        self.ui_elements = []
        self.radio_buttons = []
        self.text_inputs = []
        self.selected_building = None
        self._building_geometry_key = None
        self._generation_visual_key = None
        self.create_ui()

        # Initialize 3D components
        self.camera = OrbitCamera(target=(0.0, 0.0, 3.0), distance=25.0)
        self.renderer = BuildingRenderer()
        self.renderer.setup_gl(self.viewport_width, height)

        # Timing
        self.clock = pygame.time.Clock()
        self.running = True

    def create_ui(self):
        """Create UI elements."""
        y = 20

        # Title
        self.ui_elements.append(Label((10, y), "Buildings:", 24))
        y += 35

        # Radio buttons for building selection
        building_names = ["Small House", "Big House", "L-Shaped", "Angled House"]
        for i, name in enumerate(building_names):
            radio = RadioButton(
                pygame.Rect(10, y, 280, 30),
                name,
                lambda n=name: self.load_building_by_name(n),
                selected=(i == 0)
            )
            self.radio_buttons.append(radio)
            self.ui_elements.append(radio)
            y += 35

        # Clear button
        y += 10
        clear_btn = Button(pygame.Rect(10, y, 280, 35), "Clear", self.clear_building)
        self.ui_elements.append(clear_btn)
        y += 50

        # Parameters section
        self.ui_elements.append(Label((10, y), "Parameters:", 22))
        y += 30

        # Seed
        self.ui_elements.append(Label((10, y + 5), "Seed:", 20))
        self.seed_input = TextInput(pygame.Rect(72, y, 118, 30), "12345")
        self.ui_elements.append(self.seed_input)
        rnd_seed_btn = Button(
            pygame.Rect(195, y, 95, 30),
            "Random",
            self._random_building_seed,
        )
        self.ui_elements.append(rnd_seed_btn)
        y += 35

        # Floor Height
        self.ui_elements.append(Label((10, y + 5), "Floor Height:", 20))
        self.floor_height_input = TextInput(pygame.Rect(100, y, 190, 30), "3.0")
        self.ui_elements.append(self.floor_height_input)
        y += 35

        # Door Density
        self.ui_elements.append(Label((10, y + 5), "Door Density:", 20))
        self.door_density_input = TextInput(pygame.Rect(100, y, 190, 30), "0.05")
        self.ui_elements.append(self.door_density_input)
        y += 35

        # Upper floors: above-occlusion segments only (see docs/DOOR_GENERATION.md)
        self.ui_elements.append(Label((10, y + 5), "Upper door chance:", 20))
        self.above_occlusion_door_chance_input = TextInput(
            pygame.Rect(100, y, 190, 30), "0.65"
        )
        self.ui_elements.append(self.above_occlusion_door_chance_input)
        y += 35

        # Window Density
        self.ui_elements.append(Label((10, y + 5), "Win Density:", 20))
        self.window_density_input = TextInput(pygame.Rect(100, y, 190, 30), "0.3")
        self.ui_elements.append(self.window_density_input)
        y += 35

        # Corner Size
        self.ui_elements.append(Label((10, y + 5), "Corner Size:", 20))
        self.corner_size_input = TextInput(pygame.Rect(100, y, 190, 30), "0.15")
        self.ui_elements.append(self.corner_size_input)
        y += 35

        # Window Size
        self.ui_elements.append(Label((10, y + 5), "Window Size:", 20))
        self.window_size_input = TextInput(pygame.Rect(100, y, 190, 30), "1.2")
        self.ui_elements.append(self.window_size_input)
        y += 35

        # Floor Band
        self.ui_elements.append(Label((10, y + 5), "Floor Band:", 20))
        self.floor_band_input = TextInput(pygame.Rect(100, y, 190, 30), "0.3")
        self.ui_elements.append(self.floor_band_input)
        y += 35

        # Wall Offset (legacy - walls are now flush with footprint)
        self.ui_elements.append(Label((10, y + 5), "Wall Offset:", 20))
        self.wall_offset_input = TextInput(pygame.Rect(100, y, 190, 30), "0")
        self.ui_elements.append(self.wall_offset_input)
        y += 35

        # Reload button
        reload_btn = Button(pygame.Rect(10, y, 280, 35), "reload", self.reload_current_building)
        self.ui_elements.append(reload_btn)
        y += 50

        # Visibility section
        self.ui_elements.append(Label((10, y), "Visibility:", 22))
        y += 30

        self.footprints_checkbox = Checkbox(pygame.Rect(10, y, 280, 30), "Show Footprints", True)
        self.ui_elements.append(self.footprints_checkbox)
        y += 35

        self.doors_checkbox = Checkbox(pygame.Rect(10, y, 280, 30), "Show Doors", True)
        self.ui_elements.append(self.doors_checkbox)
        y += 35

        self.windows_checkbox = Checkbox(pygame.Rect(10, y, 280, 30), "Show Windows", True)
        self.ui_elements.append(self.windows_checkbox)
        y += 35

        self.walls_checkbox = Checkbox(pygame.Rect(10, y, 280, 30), "Show Walls", True)
        self.ui_elements.append(self.walls_checkbox)
        y += 35

        self.corners_checkbox = Checkbox(pygame.Rect(10, y, 280, 30), "Show Corners", True)
        self.ui_elements.append(self.corners_checkbox)
        y += 35

        self.roof_checkbox = Checkbox(pygame.Rect(10, y, 280, 30), "Show Roof", True)
        self.ui_elements.append(self.roof_checkbox)
        y += 35

        wire_text_inputs_blur(self.ui_elements, self._commit_building_panel)
        self.text_inputs = collect_text_inputs(self.ui_elements)

        # Load first building by default
        self.selected_building = "Small House"
        self.load_building_by_name("Small House")

    def create_building_templates(self):
        """Create predefined building templates."""
        templates = {}

        # Small House: 10x10m, 2 stories, centered at origin
        templates['Small House'] = {
            'floors': [
                [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 1
                [(-5, -5), (5, -5), (5, 5), (-5, 5)],  # Floor 2
            ],
            'floor_heights': [3.0, 3.0],
            'default_seed': 12345
        }

        # Big House: 15x15m, 4 stories, centered at origin
        templates['Big House'] = {
            'floors': [
                [(-7.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5)],  # Floor 1
                [(-7.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5)],  # Floor 2
                [(-7.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5)],  # Floor 3
                [(-7.5, -7.5), (7.5, -7.5), (7.5, 7.5), (-7.5, 7.5)],  # Floor 4
            ],
            'floor_heights': [3.5, 3.0, 3.0, 3.0],
            'default_seed': 54321
        }

        # L-Shaped Building: 12x12m with L shape, 3 stories, centered around origin
        templates['L-Shaped'] = {
            'floors': [
                [(-6, -6), (6, -6), (6, 1), (1, 1), (1, 6), (-6, 6)],  # Floor 1
                [(-6, -6), (6, -6), (6, 1), (1, 1), (1, 6), (-6, 6)],  # Floor 2
                [(-6, -6), (6, -6), (6, 1), (1, 1), (1, 6), (-6, 6)],  # Floor 3
            ],
            'floor_heights': [3.0, 3.0, 3.0],
            'default_seed': 99999
        }

        # Angled Building: Hexagonal-style with 30-60 degree angles, 3 stories
        import math
        angle_60 = math.radians(60)
        w = 5.0
        h = w * math.tan(angle_60)

        templates['Angled House'] = {
            'floors': [
                [(-5, -5), (5, -5), (5, 3), (-5, 3 + h)],
                [(-5, -5), (5, -5), (5, 3), (-5, 3 + h)],
                [(-5, -5), (5, -5), (5, 3), (-5, 3 + h)],
            ],
            'floor_heights': [3.0, 3.0, 3.0],
            'default_seed': 77777
        }

        return templates

    @staticmethod
    def _fmt_num(v: float) -> str:
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return str(v)

    def _generation_params_text_key(self) -> tuple:
        return (
            self.door_density_input.text,
            self.above_occlusion_door_chance_input.text,
            self.window_density_input.text,
            self.corner_size_input.text,
            self.window_size_input.text,
            self.floor_band_input.text,
            self.wall_offset_input.text,
        )

    def _normalize_all_building_fields(self, template: dict) -> None:
        """Fix invalid / empty numeric fields (blur / load only)."""
        dseed = template.get("default_seed", 12345)
        s = self.seed_input.text.strip()
        if not s:
            self.seed_input.text = str(dseed)
        else:
            try:
                self.seed_input.text = str(int(s))
            except ValueError:
                self.seed_input.text = str(dseed)

        fh_def = template.get("floor_heights", [3.0])[0]
        s = self.floor_height_input.text.strip()
        try:
            v = float(s) if s else fh_def
            self.floor_height_input.text = self._fmt_num(max(0.1, v))
        except ValueError:
            self.floor_height_input.text = self._fmt_num(fh_def)

        defaults = [
            (self.door_density_input, 0.05),
            (self.above_occlusion_door_chance_input, 0.65),
            (self.window_density_input, 0.3),
            (self.corner_size_input, 0.15),
            (self.window_size_input, 1.2),
            (self.floor_band_input, 0.3),
            (self.wall_offset_input, 0.0),
        ]
        for inp, dflt in defaults:
            s = inp.text.strip()
            try:
                v = float(s) if s else dflt
                inp.text = self._fmt_num(v)
            except ValueError:
                inp.text = self._fmt_num(dflt)
        try:
            u = float(self.above_occlusion_door_chance_input.text)
            u = max(0.0, min(1.0, u))
            self.above_occlusion_door_chance_input.text = self._fmt_num(u)
        except ValueError:
            self.above_occlusion_door_chance_input.text = "0.65"

    def _commit_building_panel(self) -> None:
        """Normalize fields and rebuild / clear caches when something changed (blur)."""
        if self.selected_building not in self.building_templates:
            return
        template = self.building_templates[self.selected_building]
        self._normalize_all_building_fields(template)

        new_geom = (
            self.selected_building,
            self.seed_input.text,
            self.floor_height_input.text,
        )
        new_gen = self._generation_params_text_key()

        need_reload = self.current_building is None or new_geom != self._building_geometry_key
        if need_reload:
            self.load_building_by_name(self.selected_building, quiet=True, commit=False)
        elif new_gen != self._generation_visual_key and self.current_building is not None:
            for i in range(self.current_building.num_floors):
                self.current_building.get_floor(i).clear_generated()
            self._generation_visual_key = new_gen

    def _random_building_seed(self) -> None:
        if self.selected_building not in self.building_templates:
            return
        self.seed_input.text = str(random.randint(0, 2**31 - 1))
        self.seed_input.active = False
        self.seed_input._replace_next = False
        self._commit_building_panel()

    def load_building_by_name(
        self, building_name: str, quiet: bool = False, commit: bool = True
    ):
        """Load building by name."""
        if building_name not in self.building_templates:
            print(f"Unknown building: {building_name}")
            return

        self.selected_building = building_name
        for radio in self.radio_buttons:
            radio.selected = (radio.text == building_name)

        template = self.building_templates[building_name]

        if commit:
            self._normalize_all_building_fields(template)

        seed = int(self.seed_input.text)
        floor_height = float(self.floor_height_input.text)
        floor_heights = [floor_height] * len(template["floors"])

        self.current_building = Building(
            floors=template['floors'],
            seed=seed,
            floor_heights=floor_heights
        )

        try:
            door_density = float(self.door_density_input.text)
        except (ValueError, AttributeError):
            door_density = 0.05

        try:
            window_density = float(self.window_density_input.text)
        except (ValueError, AttributeError):
            window_density = 0.3

        self._building_geometry_key = (
            self.selected_building,
            self.seed_input.text,
            self.floor_height_input.text,
        )
        self._generation_visual_key = self._generation_params_text_key()

        if not quiet:
            print(f"Loaded {building_name} with seed {seed}")
            print(f"  Floors: {self.current_building.num_floors}")
            print(f"  Floor height: {floor_height:.1f}m")
            try:
                upper_door = float(self.above_occlusion_door_chance_input.text)
            except (ValueError, AttributeError):
                upper_door = 0.65
            print(
                f"  Door density: {door_density}, upper-floor chance: {upper_door}, "
                f"Window density: {window_density}"
            )
            print(f"  Total height: {self.current_building.get_total_height():.1f}m")

    def reload_current_building(self):
        """Reload current building with new parameters."""
        if self.selected_building is None:
            print("No building selected to reload")
            return

        if self.current_building is not None:
            for i in range(self.current_building.num_floors):
                floor = self.current_building.get_floor(i)
                floor.clear_generated()

        self._building_geometry_key = None
        self._generation_visual_key = None
        print(f"\nReloading {self.selected_building} with new parameters...")
        self.load_building_by_name(self.selected_building, quiet=False, commit=True)

    def clear_building(self):
        """Clear current building."""
        self.current_building = None
        self._building_geometry_key = None
        self._generation_visual_key = None
        print("Building cleared")

    def _sync_building_geometry_from_panel(self):
        """Rebuild Building when seed or floor height changes (auto-update)."""
        if self.current_building is None:
            return
        if (
            self.selected_building is None
            or self.selected_building not in self.building_templates
        ):
            return
        key = (
            self.selected_building,
            self.seed_input.text,
            self.floor_height_input.text,
        )
        if key == self._building_geometry_key:
            return
        self.load_building_by_name(self.selected_building, quiet=True)

    def handle_events(self):
        """Handle pygame events."""
        self.clock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                blur_text_inputs_unless_clicked(self.text_inputs, event)

            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < self.ui_panel_width:
                for element in self.ui_elements:
                    if hasattr(element, 'handle_event'):
                        element.handle_event(event)

                self.renderer.show_footprints = self.footprints_checkbox.checked
                self.renderer.show_doors = self.doors_checkbox.checked
                self.renderer.show_windows = self.windows_checkbox.checked
                self.renderer.show_walls = self.walls_checkbox.checked
                self.renderer.show_corners = self.corners_checkbox.checked
                self.renderer.show_roof = self.roof_checkbox.checked
            else:
                if event.type == MOUSEBUTTONDOWN:
                    self.camera.handle_mouse_down(mouse_pos, event.button)
                elif event.type == MOUSEBUTTONUP:
                    self.camera.handle_mouse_up(mouse_pos, event.button)
                elif event.type == MOUSEMOTION:
                    self.camera.handle_mouse_motion(mouse_pos)
                elif event.type == MOUSEWHEEL:
                    self.camera.handle_mouse_wheel(event.y)

    def render(self):
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
        if self.current_building is not None:
            try:
                door_density = float(self.door_density_input.text)
            except (ValueError, AttributeError):
                door_density = 0.05

            try:
                above_occlusion_door_chance = float(
                    self.above_occlusion_door_chance_input.text
                )
            except (ValueError, AttributeError):
                above_occlusion_door_chance = 0.65
            above_occlusion_door_chance = max(
                0.0, min(1.0, above_occlusion_door_chance)
            )

            try:
                window_density = float(self.window_density_input.text)
            except (ValueError, AttributeError):
                window_density = 0.3

            try:
                corner_size = float(self.corner_size_input.text)
            except (ValueError, AttributeError):
                corner_size = 0.15

            try:
                wall_offset = float(self.wall_offset_input.text)
            except (ValueError, AttributeError):
                wall_offset = 0.0

            try:
                window_width = float(self.window_size_input.text)
            except (ValueError, AttributeError):
                window_width = 1.2

            try:
                floor_band = float(self.floor_band_input.text)
            except (ValueError, AttributeError):
                floor_band = 0.3

            generation_params = {
                'door_density': door_density,
                'above_occlusion_door_chance': above_occlusion_door_chance,
                'window_density': window_density,
                'edge_spacing': 1.0,
                'corner_size': corner_size,
                'wall_offset': wall_offset,
                'width': window_width,
                'floor_band': floor_band,
            }

            self.renderer.render_building(self.current_building, generation_params)

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

        ui_string = pygame.image.tostring(self.ui_surface, 'RGBA', True)
        glRasterPos2i(0, 0)
        glDrawPixels(self.ui_panel_width, self.height, GL_RGBA, GL_UNSIGNED_BYTE, ui_string)

        pygame.display.flip()

    def run(self):
        """Main application loop."""
        print("=== Building Viewer ===")
        print("Controls:")
        print("  - Left mouse drag: Rotate camera")
        print("  - Middle mouse drag: Pan view")
        print("  - Mouse wheel: Zoom in/out")
        print("  - Tab/Enter/click away commits fields; 3D view click unfocuses")
        print("  - Random: new seed + commit; Reload: rebuild + print summary")
        print()

        while self.running:
            self.handle_events()
            self.render()

        pygame.quit()


def main():
    """Entry point for building viewer."""
    viewer = BuildingViewer()
    viewer.run()


if __name__ == '__main__':
    main()
