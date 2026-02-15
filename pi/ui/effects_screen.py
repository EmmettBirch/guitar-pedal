# effects_screen.py - Browse and edit individual effect parameters.
# Two sub-views: a list of all effects, and a detail view with sliders
# for the selected effect's parameters.

import pygame


# Parameter registry: maps effect class name to a list of
# (display_name, attr_name, min_val, max_val, format_str)
PARAM_REGISTRY = {
    'Overdrive': [
        ('Gain',      'gain',      0.0, 20.0, '{:.1f}'),
        ('Tone',      'tone',      0.0,  1.0, '{:.2f}'),
        ('Level',     'level',     0.0,  1.0, '{:.2f}'),
    ],
    'Fuzz': [
        ('Gain',      'gain',      0.0, 30.0, '{:.1f}'),
        ('Threshold', 'threshold', 0.0,  1.0, '{:.2f}'),
        ('Tone',      'tone',      0.0,  1.0, '{:.2f}'),
        ('Level',     'level',     0.0,  1.0, '{:.2f}'),
    ],
    'Delay': [
        ('Delay ms',  'delay_ms',  0.0, 1000.0, '{:.0f}'),
        ('Feedback',  'feedback',  0.0,  1.0,   '{:.2f}'),
        ('Mix',       'mix',       0.0,  1.0,   '{:.2f}'),
    ],
    'Chorus': [
        ('Rate',  'rate',  0.1, 5.0,  '{:.2f}'),
        ('Depth', 'depth', 0.0, 0.02, '{:.4f}'),
        ('Mix',   'mix',   0.0, 1.0,  '{:.2f}'),
    ],
    'Reverb': [
        ('Room Size', 'room_size', 0.0, 1.0, '{:.2f}'),
        ('Damping',   'damping',   0.0, 1.0, '{:.2f}'),
        ('Mix',       'mix',       0.0, 1.0, '{:.2f}'),
    ],
}


class EffectsScreen:
    def __init__(self, screen, effect_chain):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.chain = effect_chain

        # Sub-view state
        self.view = 'list'          # 'list' or 'detail'
        self.selected_index = None  # Index into effect_chain.effects
        self.dragging_param = None  # Index of param being dragged (detail view)

        # Colors
        self.bg = (5, 5, 15)
        self.text = (220, 220, 220)
        self.dim_text = (120, 120, 120)
        self.blue = (0, 180, 255)
        self.card_bg = (20, 20, 40)
        self.green = (0, 200, 80)
        self.red = (180, 60, 60)
        self.dim_red = (100, 40, 40)
        self.white = (255, 255, 255)

        # Layout
        self.header_height = 45
        self.card_height = 44
        self.card_gap = 8

        # Fonts
        self.title_font = pygame.font.SysFont('monospace', 20, bold=True)
        self.item_font = pygame.font.SysFont('monospace', 16)
        self.small_font = pygame.font.SysFont('monospace', 14)
        self.badge_font = pygame.font.SysFont('monospace', 13, bold=True)

        # Back button
        self.btn_back = pygame.Rect(5, 5, 50, 32)

        # Toggle button rect (set during draw)
        self._toggle_rect = pygame.Rect(0, 0, 0, 0)

        # Slider geometry (detail view)
        self.slider_x = 140
        self.slider_w = 220
        self.slider_h = 8
        self.knob_r = 10
        self.value_x = 375

    # -- List View ---------------------------------------------------

    def _draw_list(self, dt):
        self.screen.fill(self.bg)
        self._draw_header("EFFECTS")

        effects = self.chain.effects
        start_y = self.header_height + self.card_gap
        for i, fx in enumerate(effects):
            y = start_y + i * (self.card_height + self.card_gap)
            rect = pygame.Rect(self.card_gap, y,
                               self.width - self.card_gap * 2, self.card_height)
            pygame.draw.rect(self.screen, self.card_bg, rect, border_radius=6)

            # Effect name
            name = type(fx).__name__
            label = self.item_font.render(name, True, self.text)
            self.screen.blit(label, (rect.x + 15, rect.centery - label.get_height() // 2))

            # ON/OFF badge
            badge_rect = pygame.Rect(rect.right - 60, rect.centery - 12, 45, 24)
            if fx.enabled:
                pygame.draw.rect(self.screen, self.green, badge_rect, border_radius=4)
                txt = self.badge_font.render("ON", True, (0, 0, 0))
            else:
                pygame.draw.rect(self.screen, self.dim_red, badge_rect, border_radius=4)
                txt = self.badge_font.render("OFF", True, (180, 180, 180))
            self.screen.blit(txt, txt.get_rect(center=badge_rect.center))

    def _handle_list_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.collidepoint(event.pos):
                return "back"
            effects = self.chain.effects
            start_y = self.header_height + self.card_gap
            for i in range(len(effects)):
                y = start_y + i * (self.card_height + self.card_gap)
                rect = pygame.Rect(self.card_gap, y,
                                   self.width - self.card_gap * 2, self.card_height)
                if rect.collidepoint(event.pos):
                    self.selected_index = i
                    self.view = 'detail'
                    return None
        return None

    # -- Detail View -------------------------------------------------

    def _get_params(self):
        """Return the parameter list for the currently selected effect."""
        fx = self.chain.effects[self.selected_index]
        class_name = type(fx).__name__
        return PARAM_REGISTRY.get(class_name, [])

    def _slider_rect(self, param_index):
        """Return the bounding rect for the slider track of a parameter row."""
        y = self._param_y(param_index)
        return pygame.Rect(self.slider_x, y + self.card_height // 2 - self.slider_h // 2,
                           self.slider_w, self.slider_h)

    def _param_y(self, param_index):
        """Top y of a parameter row."""
        toggle_area = 50  # space for toggle button
        return self.header_height + toggle_area + param_index * (self.card_height + self.card_gap)

    def _knob_x(self, param_index):
        """Compute the knob x position from the current parameter value."""
        fx = self.chain.effects[self.selected_index]
        params = self._get_params()
        _, attr, mn, mx, _ = params[param_index]
        val = getattr(fx, attr)
        t = (val - mn) / (mx - mn) if mx != mn else 0
        return int(self.slider_x + t * self.slider_w)

    def _draw_detail(self, dt):
        self.screen.fill(self.bg)
        fx = self.chain.effects[self.selected_index]
        name = type(fx).__name__
        self._draw_header(name)

        # Toggle button centered below header
        toggle_w, toggle_h = 120, 36
        toggle_rect = pygame.Rect(self.width // 2 - toggle_w // 2,
                                  self.header_height + 8, toggle_w, toggle_h)
        if fx.enabled:
            pygame.draw.rect(self.screen, self.green, toggle_rect, border_radius=6)
            txt = self.badge_font.render("ON", True, (0, 0, 0))
        else:
            pygame.draw.rect(self.screen, self.bg, toggle_rect, border_radius=6)
            pygame.draw.rect(self.screen, self.red, toggle_rect, 2, border_radius=6)
            txt = self.badge_font.render("OFF", True, self.red)
        self.screen.blit(txt, txt.get_rect(center=toggle_rect.center))
        self._toggle_rect = toggle_rect

        # Parameter sliders
        params = self._get_params()
        for i, (display_name, attr, mn, mx, fmt) in enumerate(params):
            y = self._param_y(i)
            cy = y + self.card_height // 2

            # Param name
            label = self.small_font.render(display_name, True, self.dim_text)
            self.screen.blit(label, (15, cy - label.get_height() // 2))

            # Slider track (background)
            track_rect = self._slider_rect(i)
            pygame.draw.rect(self.screen, (40, 40, 60), track_rect, border_radius=4)

            # Slider fill
            knob_x = self._knob_x(i)
            fill_rect = pygame.Rect(track_rect.x, track_rect.y,
                                    knob_x - track_rect.x, track_rect.height)
            pygame.draw.rect(self.screen, self.blue, fill_rect, border_radius=4)

            # Knob
            pygame.draw.circle(self.screen, self.white, (knob_x, cy), self.knob_r)

            # Value text
            val = getattr(fx, attr)
            val_str = fmt.format(val)
            val_surf = self.small_font.render(val_str, True, self.text)
            self.screen.blit(val_surf, (self.value_x, cy - val_surf.get_height() // 2))

    def _handle_detail_event(self, event):
        fx = self.chain.effects[self.selected_index]
        params = self._get_params()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.collidepoint(event.pos):
                self.view = 'list'
                self.dragging_param = None
                return None

            # Toggle button
            if self._toggle_rect.collidepoint(event.pos):
                fx.enabled = not fx.enabled
                return None

            # Check if a slider knob or track was tapped
            for i in range(len(params)):
                track = self._slider_rect(i)
                cy = self._param_y(i) + self.card_height // 2
                hit = pygame.Rect(track.x - self.knob_r, cy - self.knob_r - 5,
                                  track.width + self.knob_r * 2, self.knob_r * 2 + 10)
                if hit.collidepoint(event.pos):
                    self.dragging_param = i
                    self._apply_slider(event.pos[0], i)
                    return None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_param is not None:
                self._apply_slider(event.pos[0], self.dragging_param)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_param = None

        return None

    def _apply_slider(self, mouse_x, param_index):
        """Map mouse x to parameter value and apply it."""
        fx = self.chain.effects[self.selected_index]
        params = self._get_params()
        _, attr, mn, mx, _ = params[param_index]
        t = (mouse_x - self.slider_x) / self.slider_w
        t = max(0.0, min(1.0, t))
        val = mn + t * (mx - mn)
        setattr(fx, attr, val)

    # -- Shared ------------------------------------------------------

    def _draw_header(self, title):
        """Draw the header bar with back button and centered title."""
        pygame.draw.rect(self.screen, (24, 24, 24),
                         (0, 0, self.width, self.header_height))
        # Back button
        pygame.draw.rect(self.screen, (40, 40, 40), self.btn_back, border_radius=4)
        back = self.small_font.render("<", True, self.text)
        self.screen.blit(back, back.get_rect(center=self.btn_back.center))
        # Title
        t = self.title_font.render(title, True, self.blue)
        self.screen.blit(t, t.get_rect(center=(self.width // 2, self.header_height // 2)))
        # Divider
        pygame.draw.line(self.screen, (40, 40, 50),
                         (0, self.header_height - 1), (self.width, self.header_height - 1))

    def handle_event(self, event):
        """Route events to the active sub-view. Returns 'back' or None."""
        if self.view == 'list':
            return self._handle_list_event(event)
        else:
            return self._handle_detail_event(event)

    def draw(self, dt):
        """Draw the active sub-view."""
        if self.view == 'list':
            self._draw_list(dt)
        else:
            self._draw_detail(dt)
