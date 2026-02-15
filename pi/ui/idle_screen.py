# idle_screen.py - The idle animation that plays when no menu is open
# Shows flowing waveforms, floating particles, and a pulsing "GUITAR PEDAL" title.
# Tap anywhere on this screen to open the main menu.

import pygame
import math
import random
import time


class IdleScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.time = 0  # Tracks elapsed time for animations
        self.particles = []
        self._init_particles(60)  # Create 60 floating particles

        # Dark background color (almost black with a hint of blue)
        self.bg_color = (5, 5, 15)

        # Three wave colors that flow across the screen
        self.wave_colors = [
            (0, 180, 255),   # Blue
            (255, 0, 120),   # Pink
            (0, 255, 160),   # Green
        ]

    def _init_particles(self, count):
        """Create floating particles with random positions, speeds, and sizes."""
        for _ in range(count):
            self.particles.append({
                'x': random.uniform(0, self.width),       # Random x position
                'y': random.uniform(0, self.height),      # Random y position
                'vx': random.uniform(-0.3, 0.3),          # Horizontal speed (slow)
                'vy': random.uniform(-0.3, 0.3),          # Vertical speed (slow)
                'size': random.uniform(1, 3),              # Dot size in pixels
                'alpha': random.randint(40, 120),          # Brightness level
            })

    def _draw_wave(self, y_offset, amplitude, frequency, speed, color, thickness=2):
        """Draw a single animated sine wave across the screen.

        Args:
            y_offset:   Vertical center position of the wave
            amplitude:  How tall the wave peaks are (in pixels)
            frequency:  How many wave cycles fit across the screen
            speed:      How fast the wave moves horizontally
            color:      RGB tuple for the wave color
            thickness:  Line width in pixels
        """
        points = []
        # Calculate a y position for every 3rd pixel across the screen
        for x in range(0, self.width, 3):
            # Main sine wave
            y = y_offset + math.sin((x * frequency / self.width) + (self.time * speed)) * amplitude
            # Add a second smaller wave on top for a more organic look
            y += math.sin((x * frequency * 0.5 / self.width) + (self.time * speed * 0.7)) * (amplitude * 0.3)
            points.append((x, y))
        # Draw all the points as a connected line
        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, thickness)

    def _draw_particles(self):
        """Update and draw all floating particles. They bounce off screen edges."""
        for p in self.particles:
            # Move the particle
            p['x'] += p['vx']
            p['y'] += p['vy']

            # Bounce off screen edges by reversing direction
            if p['x'] < 0 or p['x'] > self.width:
                p['vx'] *= -1
            if p['y'] < 0 or p['y'] > self.height:
                p['vy'] *= -1

            # Pulse the brightness using a sine wave so particles twinkle
            brightness = int(p['alpha'] * (0.6 + 0.4 * math.sin(self.time * 2 + p['x'] * 0.01)))
            color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, color, (int(p['x']), int(p['y'])), int(p['size']))

    def _draw_title(self):
        """Draw the pulsing 'GUITAR PEDAL' title and 'ready' subtitle in the center."""
        # Pulse effect - smoothly fades between 70% and 100% brightness
        pulse = 0.7 + 0.3 * math.sin(self.time * 0.8)
        alpha = int(200 * pulse)

        # Main title
        font = pygame.font.SysFont('monospace', 42, bold=True)
        text = font.render('GUITAR PEDAL', True, (alpha, alpha, alpha))
        rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, rect)

        # "ready" subtitle in cyan, also pulsing
        sub_font = pygame.font.SysFont('monospace', 18)
        sub_alpha = int(120 * pulse)
        sub_text = sub_font.render('ready', True, (0, sub_alpha, sub_alpha))
        sub_rect = sub_text.get_rect(center=(self.width // 2, self.height // 2 + 40))
        self.screen.blit(sub_text, sub_rect)

    def draw(self, dt):
        """Draw one frame of the idle animation. Called 60 times per second.

        Args:
            dt: Time since the last frame in seconds (used to keep animation speed consistent)
        """
        self.time += dt

        # Clear the screen with the dark background
        self.screen.fill(self.bg_color)

        # Draw three pairs of waves (each color gets a faded background wave and a bright foreground wave)
        center_y = self.height // 2
        for i, color in enumerate(self.wave_colors):
            offset = (i - 1) * 80  # Space the waves vertically (-80, 0, +80 from center)
            faded = tuple(c // 3 for c in color)  # Dimmer version of the color
            # Background wave - thinner and dimmer
            self._draw_wave(center_y + offset, 30, 4 + i, 1.5 + i * 0.3, faded, 1)
            # Foreground wave - brighter and thicker
            self._draw_wave(center_y + offset, 20, 6 + i, 2.0 + i * 0.2, color, 2)

        # Draw the floating particles on top of the waves
        self._draw_particles()

        # Draw the title on top of everything
        self._draw_title()
