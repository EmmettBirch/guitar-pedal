# visualiser.py - Split-screen oscilloscope showing raw and processed audio signals.
# Top half shows the input waveform (blue), bottom half shows the output after
# the effect chain (green). With no effects loaded, both waveforms look identical.
# Once effects are added to the chain, the bottom waveform will show the result.

import pygame
import numpy as np


class Visualiser:
    def __init__(self, screen, signal_source, effect_chain):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.signal = signal_source         # MockSignal (or real Daisy input later)
        self.chain = effect_chain           # EffectChain to process samples through

        self.buffer_size = 1024             # Samples per frame — enough for a clear
                                            # waveform across 480px width

        # Colors matching the project's existing palette (from idle_screen.py)
        self.bg_color = (5, 5, 15)          # Dark background (almost black)
        self.input_color = (0, 180, 255)    # Blue — raw input signal
        self.output_color = (0, 255, 160)   # Green — processed output signal
        self.text_color = (220, 220, 220)   # White for general text
        self.dim_text = (120, 120, 120)     # Grey for secondary text
        self.divider_color = (40, 40, 50)   # Subtle line between panels
        self.header_bg = (24, 24, 24)       # Header bar background

        # Layout — split the screen into header + two equal waveform panels
        self.header_height = 42
        content_height = self.height - self.header_height
        self.top_y = self.header_height                         # Top panel starts here
        self.mid_y = self.header_height + content_height // 2   # Divider between panels
        self.bot_y = self.height                                # Bottom of screen

        # Back button — same size and position as Spotify screen
        self.btn_back = pygame.Rect(5, 5, 50, 32)

        # Fonts
        self.title_font = pygame.font.SysFont("monospace", 20, bold=True)
        self.label_font = pygame.font.SysFont("monospace", 12)
        self.small_font = pygame.font.SysFont("monospace", 12)

    def _draw_header(self):
        """Draw the header bar with back button and 'Visualiser' title."""
        # Header background
        pygame.draw.rect(self.screen, self.header_bg, (0, 0, self.width, self.header_height))

        # Back button — small grey rounded rectangle with "<"
        pygame.draw.rect(self.screen, (40, 40, 40), self.btn_back, border_radius=4)
        back_text = self.small_font.render("<", True, self.text_color)
        self.screen.blit(back_text, back_text.get_rect(center=self.btn_back.center))

        # "Visualiser" title in blue, centered
        title = self.title_font.render("Visualiser", True, (0, 180, 255))
        rect = title.get_rect(center=(self.width // 2, self.header_height // 2))
        self.screen.blit(title, rect)

        # Subtle divider line at the bottom of the header
        pygame.draw.line(self.screen, self.divider_color,
                         (0, self.header_height - 1), (self.width, self.header_height - 1), 1)

    def _draw_waveform(self, samples, y_center, panel_height, color):
        """Draw a waveform as connected line segments within a panel.

        Maps audio samples to screen coordinates and draws them as a continuous
        line, like an oscilloscope trace. A faint center reference line is drawn
        behind the waveform to show the zero crossing point.

        Args:
            samples:      numpy array of audio samples in [-1.0, 1.0]
            y_center:     vertical center of the waveform area (pixels)
            panel_height: height of the drawing area (pixels)
            color:        RGB tuple for the waveform line
        """
        # Use 80% of panel height for the waveform (40% above center, 40% below)
        amplitude = panel_height * 0.4
        num_samples = len(samples)

        # Map each sample to a screen coordinate
        # x: evenly spaced across the full screen width
        # y: sample value scaled by amplitude, flipped so positive goes up
        x_step = self.width / num_samples
        points = []
        for i in range(num_samples):
            x = int(i * x_step)
            y = int(y_center - samples[i] * amplitude)
            points.append((x, y))

        # Draw the waveform as connected line segments (like idle screen waves)
        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, 2)

        # Draw a faint horizontal center line for reference (zero crossing)
        pygame.draw.line(self.screen, self.divider_color, (0, y_center), (self.width, y_center), 1)

    def draw(self, dt):
        """Draw one frame of the visualiser. Called 60 times per second.

        Each frame: fetch a buffer of samples from the signal source, copy it,
        run the copy through the effect chain, then draw both as waveforms.

        Args:
            dt: Time since the last frame in seconds (unused for now, kept for consistency)
        """
        # Clear screen with dark background
        self.screen.fill(self.bg_color)

        # Get a buffer of raw samples from the signal source
        raw_samples = self.signal.get_samples(self.buffer_size)

        # Process a copy through the effect chain (copy so raw stays untouched)
        processed_samples = self.chain.process(raw_samples.copy())

        # Draw the header bar
        self._draw_header()

        # Calculate the vertical center of each waveform panel
        top_panel_height = self.mid_y - self.top_y
        bot_panel_height = self.bot_y - self.mid_y
        top_center = self.top_y + top_panel_height // 2
        bot_center = self.mid_y + bot_panel_height // 2

        # Draw input waveform (top half, blue)
        self._draw_waveform(raw_samples, top_center, top_panel_height, self.input_color)

        # Draw output waveform (bottom half, green)
        self._draw_waveform(processed_samples, bot_center, bot_panel_height, self.output_color)

        # Draw divider line between the two panels
        pygame.draw.line(self.screen, self.divider_color, (0, self.mid_y), (self.width, self.mid_y), 1)

        # Draw "Input" / "Output" labels in the top-left corner of each panel
        input_label = self.label_font.render("Input", True, self.input_color)
        self.screen.blit(input_label, (8, self.top_y + 4))

        output_label = self.label_font.render("Output", True, self.output_color)
        self.screen.blit(output_label, (8, self.mid_y + 4))

    def handle_event(self, event):
        """Handle touch events on the visualiser screen.

        Returns "back" if the back button was tapped, otherwise None.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.collidepoint(event.pos):
                return "back"
        return None
