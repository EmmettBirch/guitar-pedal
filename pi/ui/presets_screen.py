# presets_screen.py - Preset browser screen
# Three sub-views: list (browse/apply), naming (save new preset), and
# confirm_delete (delete a user preset).

import pygame
import time
from effects.presets import (get_all_presets, load_user_presets,
                             save_user_presets, snapshot_chain, apply_preset)


class PresetsScreen:
    def __init__(self, screen, effect_chain):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.chain = effect_chain

        # Sub-view state
        self.view = 'list'          # 'list', 'naming', or 'confirm_delete'
        self.presets = []            # Cached preset list
        self.delete_index = None    # Index in self.presets of preset to delete

        # Colors
        self.bg = (5, 5, 15)
        self.text = (220, 220, 220)
        self.dim_text = (120, 120, 120)
        self.blue = (0, 180, 255)
        self.card_bg = (20, 20, 40)
        self.green = (0, 200, 80)
        self.red = (180, 60, 60)
        self.white = (255, 255, 255)

        # Layout
        self.header_height = 45
        self.row_height = 44
        self.row_gap = 6
        self.padding = 8

        # Fonts
        self.title_font = pygame.font.SysFont('monospace', 20, bold=True)
        self.item_font = pygame.font.SysFont('monospace', 16)
        self.small_font = pygame.font.SysFont('monospace', 14)
        self.badge_font = pygame.font.SysFont('monospace', 13, bold=True)
        self.key_font = pygame.font.SysFont('monospace', 16, bold=True)

        # Back button
        self.btn_back = pygame.Rect(5, 5, 50, 32)

        # Touch scrolling (list view)
        self.scroll_offset = 0
        self.touch_start_y = None
        self.scrolling = False

        # Green flash feedback
        self._flash_index = None
        self._flash_time = 0

        # Naming view state
        self._name_text = ""
        self._cursor_blink = 0
        self._char_grid = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
        self._grid_cols = 13
        self._key_w = 34
        self._key_h = 40

    def refresh_presets(self):
        """Reload preset list from factory + disk."""
        self.presets = get_all_presets()
        self.scroll_offset = 0

    # -- Header ------------------------------------------------------

    def _draw_header(self, title):
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

    # -- List View ---------------------------------------------------

    def _item_rect(self, index):
        y = (self.header_height + self.row_gap
             + index * (self.row_height + self.row_gap)
             - self.scroll_offset)
        return pygame.Rect(self.padding, y,
                           self.width - self.padding * 2, self.row_height)

    def _save_btn_rect(self):
        """Rect for the '+ SAVE CURRENT' button at the bottom of the list."""
        n = len(self.presets)
        y = (self.header_height + self.row_gap
             + n * (self.row_height + self.row_gap)
             - self.scroll_offset)
        return pygame.Rect(self.padding, y,
                           self.width - self.padding * 2, self.row_height)

    def _max_scroll(self):
        total_items = len(self.presets) + 1  # +1 for save button
        content_h = total_items * (self.row_height + self.row_gap) + self.row_gap
        visible_h = self.height - self.header_height
        return max(0, content_h - visible_h)

    def _draw_list(self, dt):
        self.screen.fill(self.bg)
        self._draw_header("PRESETS")

        # Update flash timer
        if self._flash_index is not None:
            self._flash_time -= dt
            if self._flash_time <= 0:
                self._flash_index = None

        for i, preset in enumerate(self.presets):
            rect = self._item_rect(i)
            # Skip off-screen rows
            if rect.bottom < self.header_height or rect.top > self.height:
                continue

            # Green flash on recently-applied preset
            if self._flash_index == i and self._flash_time > 0:
                bg = (0, 80, 40)
            else:
                bg = self.card_bg
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)

            # Preset name
            label = self.item_font.render(preset["name"], True, self.text)
            self.screen.blit(label, (rect.x + 15, rect.centery - label.get_height() // 2))

            # Factory badge or DEL button
            if preset.get("factory"):
                badge_rect = pygame.Rect(rect.right - 80, rect.centery - 11, 65, 22)
                pygame.draw.rect(self.screen, (50, 50, 60), badge_rect, border_radius=4)
                txt = self.badge_font.render("FACTORY", True, self.dim_text)
                self.screen.blit(txt, txt.get_rect(center=badge_rect.center))
            else:
                del_rect = pygame.Rect(rect.right - 55, rect.centery - 13, 42, 26)
                pygame.draw.rect(self.screen, self.red, del_rect, border_radius=4)
                txt = self.badge_font.render("DEL", True, self.white)
                self.screen.blit(txt, txt.get_rect(center=del_rect.center))

        # "+ SAVE CURRENT" button
        save_rect = self._save_btn_rect()
        if save_rect.bottom >= self.header_height and save_rect.top <= self.height:
            pygame.draw.rect(self.screen, self.bg, save_rect, border_radius=6)
            pygame.draw.rect(self.screen, self.green, save_rect, 2, border_radius=6)
            txt = self.item_font.render("+ SAVE CURRENT", True, self.green)
            self.screen.blit(txt, txt.get_rect(center=save_rect.center))

    def _handle_list_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.collidepoint(event.pos):
                return "back"
            self.touch_start_y = event.pos[1]
            self.scrolling = False

        elif event.type == pygame.MOUSEMOTION and self.touch_start_y is not None:
            dy = event.pos[1] - self.touch_start_y
            if abs(dy) > 10:
                self.scrolling = True
                self.scroll_offset -= dy
                self.touch_start_y = event.pos[1]
                self.scroll_offset = max(0, min(self.scroll_offset, self._max_scroll()))

        elif event.type == pygame.MOUSEBUTTONUP:
            if not self.scrolling and self.touch_start_y is not None:
                pos = event.pos
                # Check save button
                if self._save_btn_rect().collidepoint(pos):
                    self._name_text = ""
                    self._cursor_blink = 0
                    self.view = 'naming'
                    self.touch_start_y = None
                    self.scrolling = False
                    return None

                # Check preset rows
                for i, preset in enumerate(self.presets):
                    rect = self._item_rect(i)
                    if rect.top < self.header_height:
                        continue
                    if rect.collidepoint(pos):
                        # Check DEL button for user presets
                        if not preset.get("factory"):
                            del_rect = pygame.Rect(rect.right - 55, rect.centery - 13, 42, 26)
                            if del_rect.collidepoint(pos):
                                self.delete_index = i
                                self.view = 'confirm_delete'
                                self.touch_start_y = None
                                self.scrolling = False
                                return None
                        # Apply preset
                        apply_preset(self.chain, preset)
                        self._flash_index = i
                        self._flash_time = 0.6
                        break

            self.touch_start_y = None
            self.scrolling = False

        return None

    # -- Naming View -------------------------------------------------

    def _draw_naming(self, dt):
        self.screen.fill(self.bg)
        self._draw_header("SAVE PRESET")
        self._cursor_blink += dt

        # Name display area
        name_y = self.header_height + 14
        name_rect = pygame.Rect(self.padding, name_y,
                                self.width - self.padding * 2, 34)
        pygame.draw.rect(self.screen, self.card_bg, name_rect, border_radius=4)
        pygame.draw.rect(self.screen, self.blue, name_rect, 1, border_radius=4)

        display = self._name_text
        # Blinking cursor
        if int(self._cursor_blink * 2) % 2 == 0:
            display += "_"
        name_surf = self.item_font.render(display, True, self.white)
        self.screen.blit(name_surf, (name_rect.x + 10,
                                     name_rect.centery - name_surf.get_height() // 2))

        # Character grid
        grid_top = name_y + 48
        grid_left = (self.width - self._grid_cols * self._key_w) // 2
        for idx, ch in enumerate(self._char_grid):
            col = idx % self._grid_cols
            row = idx // self._grid_cols
            x = grid_left + col * self._key_w
            y = grid_top + row * self._key_h
            key_rect = pygame.Rect(x + 1, y + 1, self._key_w - 2, self._key_h - 2)
            pygame.draw.rect(self.screen, (30, 30, 50), key_rect, border_radius=4)
            ch_surf = self.key_font.render(ch, True, self.text)
            self.screen.blit(ch_surf, ch_surf.get_rect(center=key_rect.center))

        # Bottom row: BACKSPACE and SAVE buttons
        btn_y = grid_top + ((len(self._char_grid) // self._grid_cols + 1) * self._key_h) + 6
        # BACKSPACE
        self._bksp_rect = pygame.Rect(self.padding, btn_y, 140, 40)
        pygame.draw.rect(self.screen, (50, 40, 40), self._bksp_rect, border_radius=6)
        bk_txt = self.item_font.render("BACKSPACE", True, self.text)
        self.screen.blit(bk_txt, bk_txt.get_rect(center=self._bksp_rect.center))

        # SAVE
        self._save_rect = pygame.Rect(self.width - self.padding - 140, btn_y, 140, 40)
        if len(self._name_text) > 0:
            pygame.draw.rect(self.screen, self.green, self._save_rect, border_radius=6)
            sv_txt = self.item_font.render("SAVE", True, (0, 0, 0))
        else:
            pygame.draw.rect(self.screen, (30, 50, 30), self._save_rect, border_radius=6)
            sv_txt = self.item_font.render("SAVE", True, (80, 80, 80))
        self.screen.blit(sv_txt, sv_txt.get_rect(center=self._save_rect.center))

    def _handle_naming_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            # Back button
            if self.btn_back.collidepoint(pos):
                self.view = 'list'
                return None

            # BACKSPACE
            if hasattr(self, '_bksp_rect') and self._bksp_rect.collidepoint(pos):
                self._name_text = self._name_text[:-1]
                return None

            # SAVE
            if (hasattr(self, '_save_rect') and self._save_rect.collidepoint(pos)
                    and len(self._name_text) > 0):
                preset = snapshot_chain(self.chain, self._name_text)
                user_presets = load_user_presets()
                user_presets.append(preset)
                save_user_presets(user_presets)
                self.refresh_presets()
                self.view = 'list'
                return None

            # Character grid
            name_y = self.header_height + 14
            grid_top = name_y + 48
            grid_left = (self.width - self._grid_cols * self._key_w) // 2
            for idx, ch in enumerate(self._char_grid):
                col = idx % self._grid_cols
                row = idx // self._grid_cols
                x = grid_left + col * self._key_w
                y = grid_top + row * self._key_h
                key_rect = pygame.Rect(x + 1, y + 1, self._key_w - 2, self._key_h - 2)
                if key_rect.collidepoint(pos) and len(self._name_text) < 12:
                    self._name_text += ch
                    return None

        return None

    # -- Delete Confirmation -----------------------------------------

    def _draw_confirm_delete(self, dt):
        # Draw the list behind the overlay (frozen)
        self._draw_list(dt)

        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Dialog box
        dw, dh = 300, 140
        dx = (self.width - dw) // 2
        dy = (self.height - dh) // 2
        dialog = pygame.Rect(dx, dy, dw, dh)
        pygame.draw.rect(self.screen, (25, 25, 45), dialog, border_radius=8)
        pygame.draw.rect(self.screen, self.blue, dialog, 2, border_radius=8)

        # Title
        title = self.item_font.render("Delete preset?", True, self.white)
        self.screen.blit(title, title.get_rect(centerx=dialog.centerx, top=dy + 15))

        # Preset name
        if self.delete_index is not None and self.delete_index < len(self.presets):
            name = self.presets[self.delete_index]["name"]
            name_surf = self.small_font.render(name, True, self.dim_text)
            self.screen.blit(name_surf, name_surf.get_rect(centerx=dialog.centerx, top=dy + 42))

        # CANCEL button
        self._cancel_rect = pygame.Rect(dx + 20, dy + dh - 50, 115, 36)
        pygame.draw.rect(self.screen, (50, 50, 60), self._cancel_rect, border_radius=6)
        c_txt = self.item_font.render("CANCEL", True, self.text)
        self.screen.blit(c_txt, c_txt.get_rect(center=self._cancel_rect.center))

        # DELETE button
        self._delete_rect = pygame.Rect(dx + dw - 135, dy + dh - 50, 115, 36)
        pygame.draw.rect(self.screen, self.red, self._delete_rect, border_radius=6)
        d_txt = self.item_font.render("DELETE", True, self.white)
        self.screen.blit(d_txt, d_txt.get_rect(center=self._delete_rect.center))

    def _handle_confirm_delete_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if hasattr(self, '_cancel_rect') and self._cancel_rect.collidepoint(pos):
                self.view = 'list'
                self.delete_index = None
                return None

            if hasattr(self, '_delete_rect') and self._delete_rect.collidepoint(pos):
                if self.delete_index is not None:
                    preset = self.presets[self.delete_index]
                    if not preset.get("factory"):
                        # Remove from user presets on disk
                        user_presets = load_user_presets()
                        user_presets = [p for p in user_presets
                                        if p["name"] != preset["name"]]
                        save_user_presets(user_presets)
                        self.refresh_presets()
                self.view = 'list'
                self.delete_index = None
                return None

        return None

    # -- Public API --------------------------------------------------

    def handle_event(self, event):
        """Route events to the active sub-view. Returns 'back' or None."""
        if self.view == 'list':
            return self._handle_list_event(event)
        elif self.view == 'naming':
            return self._handle_naming_event(event)
        elif self.view == 'confirm_delete':
            return self._handle_confirm_delete_event(event)
        return None

    def draw(self, dt):
        """Draw the active sub-view."""
        if self.view == 'list':
            self._draw_list(dt)
        elif self.view == 'naming':
            self._draw_naming(dt)
        elif self.view == 'confirm_delete':
            self._draw_confirm_delete(dt)
