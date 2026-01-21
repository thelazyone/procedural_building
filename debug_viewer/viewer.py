"""
Standalone 3D debug viewer for procedural buildings.

This is a separate application that imports the procedural_building library
and provides real-time visualization and parameter adjustment.
"""

import sys
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *

# Add parent directory to path to import procedural_building
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.building import Building
from core.floor import Floor
from debug_viewer.camera import OrbitCamera
from debug_viewer.renderer import BuildingRenderer
from debug_viewer.simple_ui import Button, Label, TextInput, Checkbox, RadioButton


class DebugViewer:
    """
    Main debug viewer application.
    
    Provides UI for building selection and 3D visualization.
    """
    
    def __init__(self, width: int = 1400, height: int = 900):
        """
        Initialize debug viewer.
        
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
        pygame.display.set_caption("Procedural Building Debug Viewer")
        
        # Create UI surface (for rendering UI separately)
        self.ui_surface = pygame.Surface((self.ui_panel_width, self.height))
        
        # Building data (create templates first, before UI)
        self.current_building = None
        self.building_templates = self.create_building_templates()
        
        # Create UI elements
        self.ui_elements = []
        self.radio_buttons = []
        self.selected_building = None
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
        building_names = ["Small House", "Big House", "L-Shaped"]
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
        
        self.ui_elements.append(Label((10, y + 5), "Seed:", 20))
        self.seed_input = TextInput(pygame.Rect(70, y, 220, 30), "12345")
        self.ui_elements.append(self.seed_input)
        y += 50
        
        # Visibility section
        self.ui_elements.append(Label((10, y), "Visibility:", 22))
        y += 30
        
        self.footprints_checkbox = Checkbox(pygame.Rect(10, y, 280, 30), "Show Footprints", True)
        self.ui_elements.append(self.footprints_checkbox)
        y += 35
        
        # Future checkboxes (not interactive yet)
        self.ui_elements.append(Label((40, y), "Show Walls (soon)", 18))
        y += 25
        self.ui_elements.append(Label((40, y), "Show Windows (soon)", 18))
        y += 25
        self.ui_elements.append(Label((40, y), "Show Doors (soon)", 18))
        y += 25
        self.ui_elements.append(Label((40, y), "Show Corners (soon)", 18))
        
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
        
        return templates
    
    def load_building_by_name(self, building_name: str):
        """Load building by name."""
        if building_name not in self.building_templates:
            print(f"Unknown building: {building_name}")
            return
        
        # Update selected building and radio buttons
        self.selected_building = building_name
        for radio in self.radio_buttons:
            radio.selected = (radio.text == building_name)
        
        template = self.building_templates[building_name]
        
        # Get seed from input
        try:
            seed = int(self.seed_input.text)
        except ValueError:
            seed = template['default_seed']
            self.seed_input.text = str(seed)
        
        # Create building
        self.current_building = Building(
            floors=template['floors'],
            seed=seed,
            floor_heights=template['floor_heights']
        )
        
        print(f"Loaded {building_name} with seed {seed}")
        print(f"  Floors: {self.current_building.num_floors}")
        print(f"  Total height: {self.current_building.get_total_height():.1f}m")
    
    def clear_building(self):
        """Clear current building."""
        self.current_building = None
        print("Building cleared")
    
    
    def handle_events(self):
        """Handle pygame events."""
        self.clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            
            # Handle UI events
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < self.ui_panel_width:
                # UI area
                for element in self.ui_elements:
                    if hasattr(element, 'handle_event'):
                        element.handle_event(event)
                
                # Update renderer visibility based on checkbox
                self.renderer.show_footprints = self.footprints_checkbox.checked
            else:
                # 3D viewport area - handle camera
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
        # Clear the entire framebuffer
        glClearColor(0.15, 0.15, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # === Render 3D viewport ===
        # Set viewport for 3D view only (right side)
        glViewport(self.viewport_x, 0, self.viewport_width, self.height)
        glScissor(self.viewport_x, 0, self.viewport_width, self.height)
        glEnable(GL_SCISSOR_TEST)
        
        # Setup projection for 3D
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        from OpenGL.GLU import gluPerspective
        gluPerspective(45, self.viewport_width / self.height, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Apply camera and render 3D scene
        self.camera.apply()
        
        # Render grid and building
        glEnable(GL_DEPTH_TEST)
        self.renderer.render_grid()
        if self.current_building is not None:
            self.renderer.render_building(self.current_building)
        
        glDisable(GL_SCISSOR_TEST)
        
        # === Render 2D UI overlay ===
        # Reset viewport to full screen
        glViewport(0, 0, self.width, self.height)
        
        # Switch to 2D orthographic projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)  # Note: 0 at bottom, height at top
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Disable depth test for flat UI
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Draw UI using pygame surface
        self.ui_surface.fill((40, 40, 40))
        for element in self.ui_elements:
            element.draw(self.ui_surface)
        
        # Convert pygame surface to OpenGL texture and blit
        ui_string = pygame.image.tostring(self.ui_surface, 'RGBA', True)
        glRasterPos2i(0, 0)
        glDrawPixels(self.ui_panel_width, self.height, GL_RGBA, GL_UNSIGNED_BYTE, ui_string)
        
        # Swap buffers
        pygame.display.flip()
    
    def run(self):
        """Main application loop."""
        print("=== Procedural Building Debug Viewer ===")
        print("Controls:")
        print("  - Left mouse drag: Rotate camera")
        print("  - Mouse wheel: Zoom in/out")
        print("  - Load button: Load selected building")
        print("  - Clear button: Clear building")
        print()
        
        while self.running:
            self.handle_events()
            self.render()
        
        pygame.quit()


def main():
    """Entry point for debug viewer."""
    viewer = DebugViewer()
    viewer.run()


if __name__ == '__main__':
    main()
