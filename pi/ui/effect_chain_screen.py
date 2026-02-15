# effect_chain_screen.py - View and reorder the effect chain.
# Shows all effects in signal-flow order with up/down buttons to reorder
# and toggle buttons to enable/disable (mute) individual effects.

import pygame


class EffectChainScreen:
    def __init__(self, screen, effect_chain):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.chain = effect_chain

        # Colors
        self.bg = (5, 5, 15)
        self.text = (220, 220, 220)
        self.dim_text = (90, 90, 110)
        self.blue = (0, 180, 255)
        self.card_bg = (20, 20, 40)
        self.card_bg_dim = (15, 15, 25)
        self.green = (0, 200, 80)
        self.dim_green = (60, 100, 60)
        self.arrow_color = (180, 180, 200)
        self.arrow_dim = (60, 60, 80)

        # Layout
        self.header_height = 45
        self.row_height = 48
        self.row_gap = 6
        self.flow_line_x = 6

        # Fonts
        self.title_font = pygame.font.SysFont('monospace', 20, bold=True)
        self.item_font = pygame.font.SysFont('monospace', 16)
        self.small_font = pygame.font.SysFont('monospace', 14)
        self.arrow_font = pygame.font.SysFont('monospace', 18, bold=True)
        self.badge_font = pygame.font.SysFont('monospace', 13, bold=True)

        # Back button
        self.btn_back = pygame.Rect(5, 5, 50, 32)

    def _row_y(self, index):
        return self.header_height + self.row_gap + index * (self.row_height + self.row_gap)

    def _draw_header(self):
        pygame.draw.rect(self.screen, (24, 24, 24),
                         (0, 0, self.width, self.header_height))
        pygame.draw.rect(self.screen, (40, 40, 40), self.btn_back, border_radius=4)
        back = self.small_font.render("<", True, self.text)
        self.screen.blit(back, back.get_rect(center=self.btn_back.center))
        t = self.title_font.render("EFFECT CHAIN", True, self.blue)
        self.screen.blit(t, t.get_rect(center=(self.width // 2, self.header_height // 2)))
        pygame.draw.line(self.screen, (40, 40, 50),
                         (0, self.header_height - 1), (self.width, self.header_height - 1))

    def _draw_signal_flow_line(self, effects):
        """Draw a thin blue vertical line at x=6 connecting enabled effects."""
        for i, fx in enumerate(effects):
            if not fx.enabled:
                continue
            y = self._row_y(i)
            cy = y + self.row_height // 2
            # Find next enabled effect
            for j in range(i + 1, len(effects)):
                if effects[j].enabled:
                    next_cy = self._row_y(j) + self.row_height // 2
                    pygame.draw.line(self.screen, self.blue,
                                     (self.flow_line_x, cy),
                                     (self.flow_line_x, next_cy), 2)
                    break

    def draw(self, dt):
        self.screen.fill(self.bg)
        self._draw_header()

        effects = self.chain.effects
        n = len(effects)

        # Signal flow line behind cards
        self._draw_signal_flow_line(effects)

        for i, fx in enumerate(effects):
            y = self._row_y(i)
            enabled = fx.enabled
            bg = self.card_bg if enabled else self.card_bg_dim
            text_color = self.text if enabled else self.dim_text

            # Card background
            card_rect = pygame.Rect(self.row_gap, y,
                                    self.width - self.row_gap * 2, self.row_height)
            pygame.draw.rect(self.screen, bg, card_rect, border_radius=6)

            cy = y + self.row_height // 2

            # Up arrow button (36x36) at x=12
            up_rect = pygame.Rect(12, cy - 18, 36, 36)
            up_color = self.arrow_color if i > 0 else self.arrow_dim
            pygame.draw.rect(self.screen, (30, 30, 50), up_rect, border_radius=4)
            up_txt = self.arrow_font.render("^", True, up_color)
            self.screen.blit(up_txt, up_txt.get_rect(center=up_rect.center))

            # Down arrow button (36x36) at x=54
            dn_rect = pygame.Rect(54, cy - 18, 36, 36)
            dn_color = self.arrow_color if i < n - 1 else self.arrow_dim
            pygame.draw.rect(self.screen, (30, 30, 50), dn_rect, border_radius=4)
            dn_txt = self.arrow_font.render("v", True, dn_color)
            self.screen.blit(dn_txt, dn_txt.get_rect(center=dn_rect.center))

            # Effect name at x=100
            name = type(fx).__name__
            label = self.item_font.render(name, True, text_color)
            self.screen.blit(label, (100, cy - label.get_height() // 2))

            # Toggle button (80x32) at x=370
            tog_rect = pygame.Rect(370, cy - 16, 80, 32)
            if enabled:
                pygame.draw.rect(self.screen, self.green, tog_rect, border_radius=4)
                tog_txt = self.badge_font.render("ON", True, (0, 0, 0))
            else:
                pygame.draw.rect(self.screen, (40, 40, 50), tog_rect, border_radius=4)
                tog_txt = self.badge_font.render("OFF", True, self.dim_text)
            self.screen.blit(tog_txt, tog_txt.get_rect(center=tog_rect.center))

    def handle_event(self, event):
        """Handle touch events. Returns 'back' or None."""
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None

        if self.btn_back.collidepoint(event.pos):
            return "back"

        effects = self.chain.effects
        n = len(effects)

        for i in range(n):
            y = self._row_y(i)
            cy = y + self.row_height // 2

            # Up arrow
            up_rect = pygame.Rect(12, cy - 18, 36, 36)
            if up_rect.collidepoint(event.pos) and i > 0:
                effects[i], effects[i - 1] = effects[i - 1], effects[i]
                return None

            # Down arrow
            dn_rect = pygame.Rect(54, cy - 18, 36, 36)
            if dn_rect.collidepoint(event.pos) and i < n - 1:
                effects[i], effects[i + 1] = effects[i + 1], effects[i]
                return None

            # Toggle button
            tog_rect = pygame.Rect(370, cy - 16, 80, 32)
            if tog_rect.collidepoint(event.pos):
                effects[i].enabled = not effects[i].enabled
                return None

        return None
