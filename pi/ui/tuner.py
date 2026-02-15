# tuner.py - Chromatic tuner screen with needle-gauge UI.
# Uses autocorrelation pitch detection on the raw input signal to find the
# current note, then displays a classic tuner gauge showing how sharp or flat
# the pitch is relative to the nearest chromatic note.

import pygame
import numpy as np
from math import log2


NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


class TunerScreen:
    def __init__(self, screen, signal_source):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.signal = signal_source
        self.sample_rate = 44100
        self.buffer_size = 4096

        # Pitch detection state
        self.current_freq = 0.0
        self.current_note = ""
        self.current_cents = 0.0
        self.detected = False

        # Smoothing — keep last N readings to average out jitter
        self.freq_history = []
        self.history_size = 5
        self.min_amplitude = 0.01  # Minimum signal level to attempt detection

        # Colors
        self.bg_color = (5, 5, 15)
        self.text_color = (220, 220, 220)
        self.dim_text = (120, 120, 120)
        self.highlight_blue = (0, 180, 255)
        self.green = (0, 230, 100)
        self.yellow = (230, 200, 0)
        self.red = (230, 60, 60)
        self.header_bg = (24, 24, 24)
        self.divider_color = (40, 40, 50)

        # Layout
        self.header_height = 45
        self.btn_back = pygame.Rect(5, 5, 50, 32)

        # Fonts
        self.title_font = pygame.font.SysFont("monospace", 20, bold=True)
        self.note_font = pygame.font.SysFont("monospace", 72, bold=True)
        self.freq_font = pygame.font.SysFont("monospace", 18)
        self.cents_font = pygame.font.SysFont("monospace", 20, bold=True)
        self.label_font = pygame.font.SysFont("monospace", 14)
        self.small_font = pygame.font.SysFont("monospace", 12)

    def _detect_pitch(self, samples):
        """Detect pitch using autocorrelation.

        Returns the detected frequency in Hz, or 0.0 if no pitch found.
        """
        # Check minimum amplitude
        if np.max(np.abs(samples)) < self.min_amplitude:
            return 0.0

        # Autocorrelation via numpy
        corr = np.correlate(samples, samples, 'full')
        corr = corr[len(corr) // 2:]  # Take second half (positive lags)

        # Normalize per-lag to correct for decreasing overlap at higher lags
        n = len(samples)
        norm = np.arange(n, 0, -1, dtype=np.float64)
        corr = corr / norm
        corr = corr / corr[0]

        min_lag = int(self.sample_rate / 1200)  # ~1200Hz upper bound
        max_lag = int(self.sample_rate / 27)    # ~27Hz lower bound (low E)

        # Clamp to valid range
        max_lag = min(max_lag, len(corr) - 1)
        if min_lag >= max_lag:
            return 0.0

        # Find first lag where correlation drops below zero (past the
        # initial peak), then search for the first positive peak after that
        search = corr[min_lag:max_lag]
        below_zero = np.where(search < 0)[0]
        if len(below_zero) == 0:
            return 0.0

        # Start searching from after the first negative region
        start = below_zero[0]

        # Find the first positive peak after the dip
        remaining = search[start:]
        above_zero = np.where(remaining > 0)[0]
        if len(above_zero) == 0:
            return 0.0

        # Within the positive region, find the maximum
        pos_start = start + above_zero[0]
        # Find where it goes negative again (or end of search)
        after_pos = search[pos_start:]
        neg_again = np.where(after_pos < 0)[0]
        if len(neg_again) > 0:
            pos_end = pos_start + neg_again[0]
        else:
            pos_end = len(search)

        peak_idx = pos_start + np.argmax(search[pos_start:pos_end])
        peak_lag = peak_idx + min_lag

        # Parabolic interpolation around the peak for sub-sample accuracy
        if 0 < peak_lag < len(corr) - 1:
            s0 = corr[peak_lag - 1]
            s1 = corr[peak_lag]
            s2 = corr[peak_lag + 1]
            denom = s0 - 2 * s1 + s2
            if denom != 0:
                adjustment = (s0 - s2) / (2 * denom)
                peak_lag = peak_lag + adjustment

        # Require minimum correlation strength at the peak
        if corr[int(round(peak_lag))] < 0.3:
            return 0.0

        freq = self.sample_rate / peak_lag
        return freq

    def _freq_to_note(self, freq):
        """Convert frequency to nearest note name, octave, and cents offset.

        Returns (note_name_with_octave, cents_offset, target_freq).
        """
        if freq <= 0:
            return ("--", 0.0, 0.0)

        # MIDI note number (69 = A4 = 440Hz)
        midi = 12 * log2(freq / 440.0) + 69
        midi_rounded = round(midi)

        # Note name and octave
        note_index = midi_rounded % 12
        octave = (midi_rounded // 12) - 1
        note_name = f"{NOTE_NAMES[note_index]}{octave}"

        # Target frequency for the nearest note
        target_freq = 440.0 * (2 ** ((midi_rounded - 69) / 12.0))

        # Cents offset from target
        cents = 1200 * log2(freq / target_freq)

        return (note_name, cents, target_freq)

    def _draw_header(self):
        """Draw header bar with back button and title."""
        pygame.draw.rect(self.screen, self.header_bg,
                         (0, 0, self.width, self.header_height))

        # Back button
        pygame.draw.rect(self.screen, (40, 40, 40), self.btn_back, border_radius=4)
        back_text = self.small_font.render("<", True, self.text_color)
        self.screen.blit(back_text, back_text.get_rect(center=self.btn_back.center))

        # Title
        title = self.title_font.render("TUNER", True, self.highlight_blue)
        rect = title.get_rect(center=(self.width // 2, self.header_height // 2))
        self.screen.blit(title, rect)

        pygame.draw.line(self.screen, self.divider_color,
                         (0, self.header_height - 1),
                         (self.width, self.header_height - 1), 1)

    def _draw_gauge(self, cents):
        """Draw the needle gauge showing cents offset from target note."""
        gauge_w = 400
        gauge_h = 60
        gauge_x = (self.width - gauge_w) // 2
        gauge_y = 235

        # Horizontal track line
        track_y = gauge_y + 20
        pygame.draw.line(self.screen, self.dim_text,
                         (gauge_x, track_y), (gauge_x + gauge_w, track_y), 2)

        # Tick marks at -50, -25, 0, +25, +50
        ticks = [-50, -25, 0, 25, 50]
        for tick_val in ticks:
            tx = gauge_x + int((tick_val + 50) / 100.0 * gauge_w)
            if tick_val == 0:
                # Center tick — taller and brighter
                pygame.draw.line(self.screen, self.text_color,
                                 (tx, track_y - 14), (tx, track_y + 14), 2)
            else:
                pygame.draw.line(self.screen, self.dim_text,
                                 (tx, track_y - 8), (tx, track_y + 8), 1)

        # "FLAT" and "SHARP" labels
        flat_label = self.label_font.render("FLAT", True, self.dim_text)
        self.screen.blit(flat_label, (gauge_x - 2, gauge_y + 42))

        sharp_label = self.label_font.render("SHARP", True, self.dim_text)
        sharp_rect = sharp_label.get_rect(topright=(gauge_x + gauge_w + 2, gauge_y + 42))
        self.screen.blit(sharp_label, sharp_rect)

        # Needle position — clamp cents to [-50, 50] range
        clamped = max(-50, min(50, cents))
        needle_x = gauge_x + int((clamped + 50) / 100.0 * gauge_w)

        # Needle color based on accuracy
        abs_cents = abs(cents)
        if abs_cents < 5:
            needle_color = self.green
        elif abs_cents < 15:
            needle_color = self.yellow
        else:
            needle_color = self.red

        # Draw needle as a small filled triangle pointing down
        tri_top = track_y - 18
        tri_w = 8
        points = [
            (needle_x, track_y - 3),           # Tip (pointing at track)
            (needle_x - tri_w, tri_top),        # Top left
            (needle_x + tri_w, tri_top),        # Top right
        ]
        pygame.draw.polygon(self.screen, needle_color, points)

        # Draw "in tune" highlight zone around center when in tune
        if abs_cents < 5 and self.detected:
            zone_w = int(10 / 100.0 * gauge_w)
            center_x = gauge_x + gauge_w // 2
            highlight_rect = pygame.Rect(center_x - zone_w // 2, track_y - 2,
                                         zone_w, 4)
            pygame.draw.rect(self.screen, (0, 230, 100, 80), highlight_rect)

    def draw(self, dt):
        """Draw one frame of the tuner screen."""
        self.screen.fill(self.bg_color)

        # Get raw samples and detect pitch
        samples = self.signal.get_samples(self.buffer_size)
        freq = self._detect_pitch(samples)

        if freq > 0:
            # Add to history for smoothing
            self.freq_history.append(freq)
            if len(self.freq_history) > self.history_size:
                self.freq_history.pop(0)

            # Use smoothed average
            smoothed_freq = sum(self.freq_history) / len(self.freq_history)
            note_name, cents, target_freq = self._freq_to_note(smoothed_freq)

            self.current_freq = smoothed_freq
            self.current_note = note_name
            self.current_cents = cents
            self.detected = True
        else:
            self.freq_history.clear()
            self.detected = False

        # Draw header
        self._draw_header()

        if self.detected:
            # Note name — large centered text
            abs_cents = abs(self.current_cents)
            note_color = self.green if abs_cents < 5 else self.text_color
            note_surf = self.note_font.render(self.current_note, True, note_color)
            note_rect = note_surf.get_rect(center=(self.width // 2, 110))
            self.screen.blit(note_surf, note_rect)

            # Frequency
            freq_text = f"{self.current_freq:.1f} Hz"
            freq_surf = self.freq_font.render(freq_text, True, self.dim_text)
            freq_rect = freq_surf.get_rect(center=(self.width // 2, 165))
            self.screen.blit(freq_surf, freq_rect)

            # Cents offset
            if self.current_cents >= 0:
                cents_text = f"+{self.current_cents:.0f}\u00a2"
            else:
                cents_text = f"{self.current_cents:.0f}\u00a2"
            cents_surf = self.cents_font.render(cents_text, True, self.dim_text)
            cents_rect = cents_surf.get_rect(center=(self.width // 2, 200))
            self.screen.blit(cents_surf, cents_rect)

            # Gauge
            self._draw_gauge(self.current_cents)
        else:
            # No signal detected
            dash_surf = self.note_font.render("--", True, self.dim_text)
            dash_rect = dash_surf.get_rect(center=(self.width // 2, 110))
            self.screen.blit(dash_surf, dash_rect)

            no_sig = self.freq_font.render("No signal", True, self.dim_text)
            no_sig_rect = no_sig.get_rect(center=(self.width // 2, 165))
            self.screen.blit(no_sig, no_sig_rect)

            # Draw empty gauge at center
            self._draw_gauge(0)

    def handle_event(self, event):
        """Handle touch events. Returns 'back' if back button tapped."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.collidepoint(event.pos):
                return "back"
        return None
