"""
Simple UI components for viewer applications (pure pygame, no pygame_gui).

Works properly with OpenGL display mode.
Shared by building_viewer and block_viewer.
"""

import pygame
from pygame.locals import K_BACKSPACE, K_DELETE, K_LEFT, K_RIGHT, K_HOME, K_END, K_RETURN, K_TAB
from typing import Optional, Callable, List, Any


def collect_text_inputs(elements: List[Any]) -> List["TextInput"]:
    """Return every TextInput instance in a flat ui_elements list."""
    return [el for el in elements if isinstance(el, TextInput)]


def wire_text_inputs_blur(elements: List[Any], callback: Callable[[], None]) -> None:
    """
    Set on_blur on all TextInput widgets in elements.

    Call once after the full panel is built so every field shares the same commit
    callback (e.g. regenerate scene on focus loss).
    """
    for el in elements:
        if isinstance(el, TextInput):
            el.on_blur = callback


def blur_text_inputs_unless_clicked(text_inputs: List["TextInput"], event: pygame.event.Event) -> None:
    """
    Deactivate any TextInput that was not clicked. Call on MOUSEBUTTONDOWN before
    dispatching to widgets so focus moves cleanly between fields.
    Invokes on_blur when a field loses focus.
    """
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return
    for t in text_inputs:
        if not t.rect.collidepoint(event.pos):
            if t.active:
                t.active = False
                t._replace_next = False
                if t.on_blur is not None:
                    t.on_blur()


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
        if self.hovered:
            pygame.draw.rect(surface, (60, 60, 60), self.rect)

        pygame.draw.circle(surface, (150, 150, 150), self.radio_center, self.radio_radius, 2)

        if self.selected:
            pygame.draw.circle(surface, (100, 200, 255), self.radio_center, self.radio_radius - 3)

        text_surf = self.font.render(self.text, True, (200, 200, 200))
        surface.blit(text_surf, (self.rect.x + 30, self.rect.y + 5))


class TextInput:
    """Simple text input widget."""

    def __init__(self, rect: pygame.Rect, default_text: str = ""):
        self.rect = rect
        self.text = default_text
        self.active = False
        # After focus, first typing replaces entire content (standard "select all" behaviour).
        self._replace_next = False
        self.font = pygame.font.Font(None, 24)
        # Called when focus is lost (click away, Enter, Tab, or blur helper).
        self.on_blur: Optional[Callable[[], None]] = None

    def _fire_blur(self) -> None:
        if self.on_blur is not None:
            self.on_blur()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle keyboard/mouse events. Returns True if handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self._replace_next = True
                return True
            return False

        if self.active and event.type == pygame.KEYDOWN:
            if event.key == K_RETURN or event.key == K_TAB:
                self.active = False
                self._replace_next = False
                self._fire_blur()
                return True

            if self._replace_next:
                if event.key in (K_LEFT, K_RIGHT, K_HOME, K_END):
                    self._replace_next = False
                    return True
                if event.key == K_BACKSPACE or event.key == K_DELETE:
                    self.text = ""
                    self._replace_next = False
                    return True
                if event.unicode and event.unicode.isprintable():
                    self.text = event.unicode
                    self._replace_next = False
                    return True
                return True

            if event.key == K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == K_DELETE:
                if self.text:
                    self.text = self.text[:-1]
            elif event.unicode and event.unicode.isprintable():
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
        pygame.draw.rect(surface, (80, 80, 80), self.checkbox_rect)
        pygame.draw.rect(surface, (150, 150, 150), self.checkbox_rect, 2)

        if self.checked:
            pygame.draw.line(surface, (100, 255, 100),
                           (self.checkbox_rect.x + 3, self.checkbox_rect.centery),
                           (self.checkbox_rect.centerx, self.checkbox_rect.bottom - 5), 3)
            pygame.draw.line(surface, (100, 255, 100),
                           (self.checkbox_rect.centerx, self.checkbox_rect.bottom - 5),
                           (self.checkbox_rect.right - 3, self.checkbox_rect.y + 3), 3)

        text_surf = self.font.render(self.text, True, (200, 200, 200))
        surface.blit(text_surf, (self.checkbox_rect.right + 10, self.rect.y + 5))
