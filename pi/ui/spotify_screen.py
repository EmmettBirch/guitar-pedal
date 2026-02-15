# spotify_screen.py - The Spotify "Now Playing" screen
# Shows the current track with album art, artist info, progress bar, and playback controls.
# Uses Spotify's dark theme colors (dark grey background, green accents).

import pygame
import time
import threading
import requests
import io


class SpotifyScreen:
    def __init__(self, screen, spotify_client):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.spotify = spotify_client   # SpotifyClient instance for API calls
        self.time_counter = 0

        # Spotify's official color palette
        self.bg_color = (18, 18, 18)         # Dark background (Spotify's dark grey)
        self.card_bg = (40, 40, 40)           # Card/button background
        self.text_color = (255, 255, 255)     # White text
        self.spotify_green = (30, 215, 96)    # Spotify's signature green
        self.dim_text = (179, 179, 179)       # Grey for secondary text
        self.bar_bg = (80, 80, 80)            # Progress bar background
        self.header_height = 42

        # Fonts at various sizes
        self.title_font = pygame.font.SysFont("monospace", 20, bold=True)
        self.track_font = pygame.font.SysFont("monospace", 18, bold=True)
        self.artist_font = pygame.font.SysFont("monospace", 15)
        self.small_font = pygame.font.SysFont("monospace", 12)
        self.btn_font = pygame.font.SysFont("monospace", 28, bold=True)
        self.auth_font = pygame.font.SysFont("monospace", 11)

        # Track data fetched from Spotify API
        self.current_track = None
        self.last_fetch = 0           # Time of last API call
        self.fetch_interval = 2       # Seconds between API calls (don't spam the API)

        # Control button positions - calculated from screen size
        btn_y = self.height - 90
        center_x = self.width // 2

        # Play/pause button - big green circle in the center
        self.play_center = (center_x, btn_y + 25)
        self.play_radius = 32

        # Previous and next buttons - smaller circles on either side
        self.prev_center = (center_x - 90, btn_y + 25)
        self.next_center = (center_x + 90, btn_y + 25)
        self.skip_radius = 24

        # Back button in the top-left corner
        self.btn_back = pygame.Rect(5, 5, 50, 32)

        # Auth state (used when Spotify isn't connected yet)
        self.auth_url = None

        # Album art cache - stores the downloaded image so we don't re-download every frame
        self.album_art_surface = None  # The pygame image surface
        self.album_art_url = None      # URL of the currently cached image

    def _draw_header(self):
        """Draw the header bar with back button and 'Spotify' title."""
        pygame.draw.rect(self.screen, (24, 24, 24), (0, 0, self.width, self.header_height))

        # Back button - small grey rectangle with "<"
        pygame.draw.rect(self.screen, self.card_bg, self.btn_back, border_radius=4)
        back_text = self.small_font.render("<", True, self.text_color)
        self.screen.blit(back_text, back_text.get_rect(center=self.btn_back.center))

        # "Spotify" title in green
        title = self.title_font.render("Spotify", True, self.spotify_green)
        rect = title.get_rect(center=(self.width // 2, self.header_height // 2))
        self.screen.blit(title, rect)

        # Subtle divider line at the bottom of the header
        pygame.draw.line(self.screen, (40, 40, 40), (0, self.header_height - 1), (self.width, self.header_height - 1), 1)

    def _draw_auth_screen(self):
        """Draw the authentication instructions screen (shown when Spotify isn't connected yet)."""
        self.screen.fill(self.bg_color)
        self._draw_header()

        # Display step-by-step instructions for connecting Spotify
        y = 70
        lines = [
            "To connect Spotify:",
            "",
            "1. On your PC, open:",
            "",
        ]
        # Break the long auth URL into multiple lines so it fits the screen
        if self.auth_url:
            lines.append(self.auth_url[:45])
            if len(self.auth_url) > 45:
                lines.append(self.auth_url[45:90])
                if len(self.auth_url) > 90:
                    lines.append(self.auth_url[90:])
        lines += [
            "",
            "2. Log in and authorize",
            "",
            "3. Copy the redirect URL",
            "   and run on your PC:",
            "   ssh <user>@<pi-ip>",
            "   python3 ~/guitar-pedal/",
            "   pi/spotify_auth.py <URL>",
        ]
        for line in lines:
            text = self.auth_font.render(line, True, self.text_color if line else self.dim_text)
            self.screen.blit(text, (15, y))
            y += 16

    def _truncate_text(self, text, font, max_width):
        """Shorten text with '...' if it's too wide to fit on screen."""
        if font.size(text)[0] <= max_width:
            return text
        while font.size(text + "...")[0] > max_width and len(text) > 0:
            text = text[:-1]
        return text + "..."

    def _draw_now_playing(self):
        """Draw the main now-playing screen with track info, progress bar, and controls."""
        self.screen.fill(self.bg_color)
        self._draw_header()

        # Show a message if nothing is playing
        if self.current_track is None:
            no_track = self.artist_font.render("Nothing playing", True, self.dim_text)
            rect = no_track.get_rect(center=(self.width // 2, self.height // 2 - 40))
            self.screen.blit(no_track, rect)
            self._draw_controls(False)
            return

        track = self.current_track
        max_text_width = self.width - 40  # Leave some padding on the sides

        # Album art - centered at the top
        art_size = 100
        art_x = (self.width - art_size) // 2
        art_y = 52

        if self.album_art_surface:
            # Draw the downloaded album art
            self.screen.blit(self.album_art_surface, (art_x, art_y))
        else:
            # Placeholder - grey square with a # symbol
            pygame.draw.rect(self.screen, self.card_bg, (art_x, art_y, art_size, art_size), border_radius=4)
            note_font = pygame.font.SysFont("monospace", 36)
            note = note_font.render("#", True, (80, 80, 80))
            self.screen.blit(note, note.get_rect(center=(art_x + art_size // 2, art_y + art_size // 2)))

        # Track name - white, bold, centered below the album art
        name = self._truncate_text(track["name"], self.track_font, max_text_width)
        name_surface = self.track_font.render(name, True, self.text_color)
        name_rect = name_surface.get_rect(center=(self.width // 2, art_y + art_size + 18))
        self.screen.blit(name_surface, name_rect)

        # Artist name - grey, centered below the track name
        artist = self._truncate_text(track["artist"], self.artist_font, max_text_width)
        artist_surface = self.artist_font.render(artist, True, self.dim_text)
        artist_rect = artist_surface.get_rect(center=(self.width // 2, art_y + art_size + 40))
        self.screen.blit(artist_surface, artist_rect)

        # Progress bar - shows how far through the track we are
        bar_y = art_y + art_size + 60
        bar_h = 4
        bar_x = 30
        bar_w = self.width - 60

        # Background bar (grey)
        pygame.draw.rect(self.screen, self.bar_bg, (bar_x, bar_y, bar_w, bar_h), border_radius=2)

        if track["duration_ms"] > 0:
            # Green fill showing progress
            progress = track["progress_ms"] / track["duration_ms"]  # 0.0 to 1.0
            fill_w = max(1, int(bar_w * progress))
            pygame.draw.rect(self.screen, self.spotify_green, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
            # Small green dot at the current position (like Spotify's slider)
            dot_x = bar_x + fill_w
            pygame.draw.circle(self.screen, self.spotify_green, (dot_x, bar_y + bar_h // 2), 5)

        # Time labels - current time on the left, total time on the right
        current_time = self._format_time(track["progress_ms"])
        total_time = self._format_time(track["duration_ms"])
        cur_text = self.small_font.render(current_time, True, self.dim_text)
        tot_text = self.small_font.render(total_time, True, self.dim_text)
        self.screen.blit(cur_text, (bar_x, bar_y + 10))
        self.screen.blit(tot_text, tot_text.get_rect(topright=(bar_x + bar_w, bar_y + 10)))

        # Draw the playback control buttons
        self._draw_controls(track["is_playing"])

    def _draw_controls(self, is_playing):
        """Draw the previous, play/pause, and next buttons."""
        # Previous button - outlined circle with "<<"
        pygame.draw.circle(self.screen, self.dim_text, self.prev_center, self.skip_radius, 2)
        prev_text = self.btn_font.render("<<", True, self.text_color)
        self.screen.blit(prev_text, prev_text.get_rect(center=self.prev_center))

        # Play/pause button - big filled green circle (like Spotify's play button)
        pygame.draw.circle(self.screen, self.spotify_green, self.play_center, self.play_radius)
        play_label = "||" if is_playing else " >"  # Show pause icon when playing, play icon when paused
        play_text = self.btn_font.render(play_label, True, (0, 0, 0))  # Black text on green
        self.screen.blit(play_text, play_text.get_rect(center=self.play_center))

        # Next button - outlined circle with ">>"
        pygame.draw.circle(self.screen, self.dim_text, self.next_center, self.skip_radius, 2)
        next_text = self.btn_font.render(">>", True, self.text_color)
        self.screen.blit(next_text, next_text.get_rect(center=self.next_center))

    def _format_time(self, ms):
        """Convert milliseconds to a 'minutes:seconds' string (e.g. 3:45)."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def _point_in_circle(self, point, center, radius):
        """Check if a touch point is inside a circular button (using distance formula)."""
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        return (dx * dx + dy * dy) <= (radius * radius)

    def handle_event(self, event):
        """Handle touch events on the Spotify screen.

        Returns "back" if the back button was tapped, otherwise None.
        Playback controls (prev/play/next) are handled directly via the Spotify API.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            # Back button - return to the menu
            if self.btn_back.collidepoint(pos):
                return "back"

            # Playback control buttons - each runs in a separate thread
            # so the UI doesn't freeze while waiting for the API response
            if self.spotify.authenticated:
                if self._point_in_circle(pos, self.prev_center, self.skip_radius + 10):
                    threading.Thread(target=self.spotify.previous_track, daemon=True).start()
                elif self._point_in_circle(pos, self.play_center, self.play_radius + 10):
                    threading.Thread(target=self.spotify.play_pause, daemon=True).start()
                elif self._point_in_circle(pos, self.next_center, self.skip_radius + 10):
                    threading.Thread(target=self.spotify.next_track, daemon=True).start()
        return None

    def draw(self, dt):
        """Draw one frame of the Spotify screen. Called 60 times per second."""
        self.time_counter += dt

        # If not authenticated, show the login instructions
        if not self.spotify.authenticated:
            if not self.auth_url:
                self.auth_url = self.spotify.get_auth_url()
            self._draw_auth_screen()
            return

        # Fetch updated track data from Spotify every 2 seconds
        # (runs in a background thread so it doesn't block the UI)
        if self.time_counter - self.last_fetch > self.fetch_interval:
            self.last_fetch = self.time_counter
            threading.Thread(target=self._fetch_track, daemon=True).start()

        # Draw the now playing screen
        self._draw_now_playing()

    def _fetch_track(self):
        """Fetch the current track from Spotify API (runs in a background thread)."""
        self.current_track = self.spotify.get_current_track()

        # If the track has album art and it's a different image than what we have cached, download it
        if self.current_track and self.current_track.get("album_art_url"):
            art_url = self.current_track["album_art_url"]
            if art_url != self.album_art_url:
                self.album_art_url = art_url
                self._load_album_art(art_url)

    def _load_album_art(self, url):
        """Download album art from Spotify and convert it to a pygame image surface."""
        try:
            response = requests.get(url, timeout=5)             # Download the image
            image_data = io.BytesIO(response.content)           # Wrap bytes in a file-like object
            image = pygame.image.load(image_data)               # Load as a pygame surface
            self.album_art_surface = pygame.transform.smoothscale(image, (100, 100))  # Resize to 100x100
        except Exception as e:
            print(f"Album art error: {e}")
            self.album_art_surface = None
