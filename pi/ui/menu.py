# menu.py - The main menu screen
# Displays a scrollable list of options that can be tapped to select.
# Supports touch scrolling and tap selection on the LCD touchscreen.

import pygame
import math


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.time = 0

        # Color scheme - dark theme with blue accents
        self.bg_color = (5, 5, 15)              # Dark background
        self.text_color = (220, 220, 220)        # Light grey text
        self.highlight_color = (0, 180, 255)     # Blue highlight for selected items
        self.item_bg = (20, 20, 40)              # Dark card background
        self.item_hover = (30, 30, 60)           # Slightly lighter when selected

        # Each menu item has a label (display text) and an icon (single character)
        self.items = [
            {'label': 'Effects', 'icon': '~'},
            {'label': 'Effect Chain', 'icon': '+'},
            {'label': 'Tuner', 'icon': '#'},
            {'label': 'Presets', 'icon': '*'},
            {'label': 'Visualiser', 'icon': '|'},
            {'label': 'Spotify', 'icon': 'S'},
            {'label': 'Exit', 'icon': 'X'},
        ]

        self.selected = None          # Index of currently selected item (None = nothing selected)
        self.scroll_offset = 0        # How far the list has been scrolled (in pixels)
        self.item_height = 44         # Height of each menu item in pixels
        self.padding = 8              # Space between items
        self.header_height = 45       # Height of the title bar at the top
        self.active = True

        # Fonts for different text sizes
        self.title_font = pygame.font.SysFont('monospace', 22, bold=True)
        self.item_font = pygame.font.SysFont('monospace', 18)
        self.icon_font = pygame.font.SysFont('monospace', 20, bold=True)

        # Touch tracking - used to tell the difference between a tap and a scroll
        self.touch_start_y = None     # Y position where the touch started
        self.scrolling = False        # True if the user is dragging to scroll

    def _get_item_rect(self, index):
        """Calculate the screen rectangle for a menu item at the given index."""
        y = self.header_height + self.padding + (index * (self.item_height + self.padding)) - self.scroll_offset
        return pygame.Rect(self.padding, y, self.width - self.padding * 2, self.item_height)

    def _draw_header(self):
        """Draw the title bar at the top of the menu."""
        pygame.draw.rect(self.screen, (10, 10, 25), (0, 0, self.width, self.header_height))
        pygame.draw.line(self.screen, self.highlight_color, (0, self.header_height), (self.width, self.header_height), 1)

        title = self.title_font.render('GUITAR PEDAL', True, self.highlight_color)
        rect = title.get_rect(center=(self.width // 2, self.header_height // 2))
        self.screen.blit(title, rect)

    def _draw_item(self, index, item):
        """Draw a single menu item card with icon, label, and arrow."""
        rect = self._get_item_rect(index)

        # Skip drawing items that have scrolled off screen
        if rect.bottom < self.header_height or rect.top > self.height:
            return

        # Use a lighter background color if this item is selected
        is_selected = self.selected == index
        bg = self.item_hover if is_selected else self.item_bg
        pygame.draw.rect(self.screen, bg, rect, border_radius=6)

        # Draw a blue border around the selected item
        if is_selected:
            pygame.draw.rect(self.screen, self.highlight_color, rect, 2, border_radius=6)

        # Draw the icon on the left side
        icon_color = self.highlight_color if is_selected else (100, 100, 140)
        icon_surface = self.icon_font.render(item['icon'], True, icon_color)
        icon_rect = icon_surface.get_rect(midleft=(rect.x + 15, rect.centery))
        self.screen.blit(icon_surface, icon_rect)

        # Draw the label text next to the icon
        label_color = self.highlight_color if is_selected else self.text_color
        label_surface = self.item_font.render(item['label'], True, label_color)
        label_rect = label_surface.get_rect(midleft=(rect.x + 45, rect.centery))
        self.screen.blit(label_surface, label_rect)

        # Draw a ">" arrow on the right side
        arrow = self.item_font.render('>', True, icon_color)
        arrow_rect = arrow.get_rect(midright=(rect.right - 15, rect.centery))
        self.screen.blit(arrow, arrow_rect)

    def handle_event(self, event):
        """Handle touch events. Returns the label of a selected item, or None.

        Touch logic:
        - On touch down: record the start position and highlight the tapped item
        - On touch move: if the finger moves more than 10px, treat it as a scroll
        - On touch up: if we didn't scroll, treat it as a tap and return the selected item
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.touch_start_y = event.pos[1]
            self.scrolling = False

            # Check which item was tapped
            for i in range(len(self.items)):
                rect = self._get_item_rect(i)
                if rect.collidepoint(event.pos) and rect.top >= self.header_height:
                    self.selected = i

        elif event.type == pygame.MOUSEMOTION and self.touch_start_y is not None:
            # Check if the finger has moved enough to count as a scroll
            dy = event.pos[1] - self.touch_start_y
            if abs(dy) > 10:
                self.scrolling = True
                self.scroll_offset -= dy  # Move the list in the opposite direction of the drag
                self.touch_start_y = event.pos[1]

                # Don't let the user scroll past the top or bottom of the list
                max_scroll = max(0, len(self.items) * (self.item_height + self.padding) - (self.height - self.header_height - self.padding))
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        elif event.type == pygame.MOUSEBUTTONUP:
            # If the user tapped (didn't scroll), return the selected item's label
            if not self.scrolling and self.selected is not None:
                return self.items[self.selected]['label']
            self.touch_start_y = None
            self.scrolling = False

        return None

    def draw(self, dt):
        """Draw one frame of the menu. Called 60 times per second."""
        self.time += dt
        self.screen.fill(self.bg_color)
        self._draw_header()

        # Draw each menu item
        for i, item in enumerate(self.items):
            self._draw_item(i, item)
