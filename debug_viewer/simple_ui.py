"""
Simple UI components for debug viewer (pure pygame, no pygame_gui).

Works properly with OpenGL display mode.
"""

import pygame
from typing import Optional, Callable, List


class Button:
    """Simple button widget."""
    
    def __init__(self, rect: pygame.Rect, text: str, callback: Callable):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.hovered = False
        self.font = pygame.font.Font(None, 24)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        return False
    
    def draw(self, surface: pygame.Surface):
        """Draw button."""
        color = (100, 100, 100) if self.hovered else (70, 70, 70)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2)
        
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class RadioButton:
    """Simple radio button widget."""
    
    def __init__(self, rect: pygame.Rect, text: str, callback: Callable, selected: bool = False):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.selected = selected
        self.hovered = False
        self.font = pygame.font.Font(None, 22)
        self.radio_center = (rect.x + 15, rect.y + 15)
        self.radio_radius = 8
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        return False
    
    def draw(self, surface: pygame.Surface):
        """Draw radio button."""
        # Highlight on hover
        if self.hovered:
            pygame.draw.rect(surface, (60, 60, 60), self.rect)
        
        # Draw outer circle
        pygame.draw.circle(surface, (150, 150, 150), self.radio_center, self.radio_radius, 2)
        
        # Draw filled circle if selected
        if self.selected:
            pygame.draw.circle(surface, (100, 200, 255), self.radio_center, self.radio_radius - 3)
        
        # Draw text
        text_surf = self.font.render(self.text, True, (200, 200, 200))
        surface.blit(text_surf, (self.rect.x + 30, self.rect.y + 5))


class TextInput:
    """Simple text input widget."""
    
    def __init__(self, rect: pygame.Rect, default_text: str = ""):
        self.rect = rect
        self.text = default_text
        self.active = False
        self.font = pygame.font.Font(None, 24)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle keyboard/mouse events. Returns True if handled."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            return self.active
        
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            return True
        return False
    
    def draw(self, surface: pygame.Surface):
        """Draw text input."""
        color = (60, 60, 60) if self.active else (50, 50, 50)
        pygame.draw.rect(surface, color, self.rect)
        border_color = (150, 150, 255) if self.active else (100, 100, 100)
        pygame.draw.rect(surface, border_color, self.rect, 2)
        
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))


class Label:
    """Simple text label."""
    
    def __init__(self, pos: tuple, text: str, size: int = 20):
        self.pos = pos
        self.text = text
        self.font = pygame.font.Font(None, size)
        
    def draw(self, surface: pygame.Surface):
        """Draw label."""
        text_surf = self.font.render(self.text, True, (200, 200, 200))
        surface.blit(text_surf, self.pos)


class Checkbox:
    """Simple checkbox widget."""
    
    def __init__(self, rect: pygame.Rect, text: str, checked: bool = False):
        self.rect = rect
        self.text = text
        self.checked = checked
        self.font = pygame.font.Font(None, 22)
        self.checkbox_rect = pygame.Rect(rect.x + 10, rect.y + 5, 20, 20)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                return True
        return False
    
    def draw(self, surface: pygame.Surface):
        """Draw checkbox."""
        # Draw box
        pygame.draw.rect(surface, (80, 80, 80), self.checkbox_rect)
        pygame.draw.rect(surface, (150, 150, 150), self.checkbox_rect, 2)
        
        # Draw check if checked
        if self.checked:
            pygame.draw.line(surface, (100, 255, 100),
                           (self.checkbox_rect.x + 3, self.checkbox_rect.centery),
                           (self.checkbox_rect.centerx, self.checkbox_rect.bottom - 5), 3)
            pygame.draw.line(surface, (100, 255, 100),
                           (self.checkbox_rect.centerx, self.checkbox_rect.bottom - 5),
                           (self.checkbox_rect.right - 3, self.checkbox_rect.y + 3), 3)
        
        # Draw text
        text_surf = self.font.render(self.text, True, (200, 200, 200))
        surface.blit(text_surf, (self.checkbox_rect.right + 10, self.rect.y + 5))
