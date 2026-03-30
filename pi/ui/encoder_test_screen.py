# encoder_test_screen.py - Visual test screen for rotary encoders.
# Shows live feedback for both encoders: rotation direction, click, and a recent event log.

import pygame
from collections import deque

from hardware.encoders import ENC1_ROTATE, ENC1_CLICK, ENC2_ROTATE, ENC2_CLICK


class EncoderTestScreen:
    MAX_LOG = 8
    FLASH_DURATION = 0.3

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.bg_color  = (5, 5, 15)
        self.highlight = (0, 180, 255)
        self.inactive  = (40, 40, 70)
        self.text_color = (220, 220, 220)
        self.dim_color = (100, 100, 130)
        self.green     = (0, 220, 100)
        self.red       = (220, 60, 60)

        self.title_font = pygame.font.SysFont('monospace', 20, bold=True)
        self.label_font = pygame.font.SysFont('monospace', 16, bold=True)
        self.log_font   = pygame.font.SysFont('monospace', 13)
        self.small_font = pygame.font.SysFont('monospace', 14, bold=True)
        self.hint_font  = pygame.font.SysFont('monospace', 12)

        self.btn_back = pygame.Rect(5, 5, 50, 32)

        self.enc = [
            {'rotate_timer': 0.0, 'click_timer': 0.0, 'last_dir': 0, 'count': 0},
            {'rotate_timer': 0.0, 'click_timer': 0.0, 'last_dir': 0, 'count': 0},
        ]
        self.log = deque(maxlen=self.MAX_LOG)

    def _add_log(self, msg):
        self.log.appendleft(msg)

    def handle_event(self, event):
        if event.type == ENC1_ROTATE:
            self.enc[0]['rotate_timer'] = self.FLASH_DURATION
            self.enc[0]['last_dir'] = event.delta
            self.enc[0]['count'] += event.delta
            self._add_log('ENC1 ' + ('CW' if event.delta > 0 else 'CCW') + '  (count=' + str(self.enc[0]['count']) + ')')
            return None
        if event.type == ENC1_CLICK:
            self.enc[0]['click_timer'] = self.FLASH_DURATION
            self._add_log('ENC1 CLICK')
            return None
        if event.type == ENC2_ROTATE:
            self.enc[1]['rotate_timer'] = self.FLASH_DURATION
            self.enc[1]['last_dir'] = event.delta
            self.enc[1]['count'] += event.delta
            self._add_log('ENC2 ' + ('CW' if event.delta > 0 else 'CCW') + '  (count=' + str(self.enc[1]['count']) + ')')
            return None
        if event.type == ENC2_CLICK:
            self.enc[1]['click_timer'] = self.FLASH_DURATION
            self._add_log('ENC2 CLICK  [back]')
            return 'back'
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.collidepoint(event.pos):
                return 'back'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'back'
        return None

    def draw(self, dt):
        for e in self.enc:
            e['rotate_timer'] = max(0.0, e['rotate_timer'] - dt)
            e['click_timer']  = max(0.0, e['click_timer']  - dt)
        self.screen.fill(self.bg_color)
        self._draw_header()
        self._draw_encoders()
        self._draw_log()

    def _draw_header(self):
        header_h = 40
        pygame.draw.rect(self.screen, (10, 10, 25), (0, 0, self.width, header_h))
        pygame.draw.line(self.screen, self.highlight, (0, header_h), (self.width, header_h), 1)
        pygame.draw.rect(self.screen, (40, 40, 40), self.btn_back, border_radius=4)
        back = self.small_font.render('<', True, self.text_color)
        self.screen.blit(back, back.get_rect(center=self.btn_back.center))
        surf = self.title_font.render('ENCODER TEST', True, self.highlight)
        self.screen.blit(surf, surf.get_rect(center=(self.width // 2, header_h // 2)))

    def _draw_encoders(self):
        top = 55
        widget_w = (self.width - 30) // 2
        widget_h = 130

        for i, e in enumerate(self.enc):
            x = 10 + i * (widget_w + 10)
            rect = pygame.Rect(x, top, widget_w, widget_h)

            active = e['rotate_timer'] > 0 or e['click_timer'] > 0
            border_col = self.highlight if active else self.inactive
            pygame.draw.rect(self.screen, (15, 15, 30), rect, border_radius=8)
            pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=8)

            label = self.label_font.render('ENC' + str(i + 1), True, self.highlight)
            self.screen.blit(label, label.get_rect(centerx=rect.centerx, top=rect.top + 8))

            arrow_y = rect.top + 42

            # CCW arrow (left)
            lit_ccw = e['rotate_timer'] > 0 and e['last_dir'] == -1
            col_ccw = self.red if lit_ccw else self.dim_color
            surf_ccw = self.label_font.render('<<', True, col_ccw)
            self.screen.blit(surf_ccw, surf_ccw.get_rect(midleft=(rect.left + 14, arrow_y)))

            # CW arrow (right)
            lit_cw = e['rotate_timer'] > 0 and e['last_dir'] == 1
            col_cw = self.green if lit_cw else self.dim_color
            surf_cw = self.label_font.render('>>', True, col_cw)
            self.screen.blit(surf_cw, surf_cw.get_rect(midright=(rect.right - 14, arrow_y)))

            count_surf = self.hint_font.render('count: ' + str(e['count']), True, self.dim_color)
            self.screen.blit(count_surf, count_surf.get_rect(centerx=rect.centerx, top=arrow_y + 20))

            click_lit = e['click_timer'] > 0
            btn_col = self.highlight if click_lit else self.inactive
            btn_rect = pygame.Rect(rect.centerx - 30, arrow_y + 42, 60, 26)
            pygame.draw.rect(self.screen, btn_col, btn_rect, border_radius=5)
            click_label = self.hint_font.render('CLICK', True, self.bg_color if click_lit else self.dim_color)
            self.screen.blit(click_label, click_label.get_rect(center=btn_rect.center))

    def _draw_log(self):
        log_top = 200
        header = self.hint_font.render('Recent events:', True, self.dim_color)
        self.screen.blit(header, (10, log_top))
        for i, entry in enumerate(self.log):
            col = self.text_color if i == 0 else self.dim_color
            surf = self.log_font.render(entry, True, col)
            self.screen.blit(surf, (10, log_top + 16 + i * 16))
