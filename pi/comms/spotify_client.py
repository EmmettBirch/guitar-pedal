# spotify_client.py - Handles all communication with the Spotify API
# Uses the 'spotipy' library to authenticate and control Spotify playback.
# Credentials are loaded from the .env file (not stored in code for security).

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables from the .env file (contains SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import threading
import http.server
import ssl
import urllib.parse

# Path to store the cached Spotify auth token (so you don't have to log in every time)
CACHE_PATH = os.path.expanduser('~/.spotify_cache')

# Spotify API credentials - loaded from .env file, NOT hardcoded
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', '')

# Where Spotify redirects after login - must match what's set in the Spotify Developer Dashboard
REDIRECT_URI = 'http://127.0.0.1:8888/callback'

# Permissions we need from Spotify:
# - user-read-playback-state: see what's currently playing
# - user-modify-playback-state: play, pause, skip tracks
# - user-read-currently-playing: get the current track info
SCOPE = 'user-read-playback-state user-modify-playback-state user-read-currently-playing'


class SpotifyClient:
    def __init__(self):
        self.sp = None  # The Spotify API client (None until authenticated)

        # Set up the OAuth authentication manager
        self.auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=CACHE_PATH,      # Save the token to disk so it persists between restarts
            open_browser=False,          # Don't try to open a browser (we're on a headless Pi)
        )
        self.auth_url = None
        self.authenticated = False

        # Check if we already have a valid token saved from a previous session
        self._try_cached_token()

    def _try_cached_token(self):
        """Check if there's a saved token we can reuse (avoids needing to log in again)."""
        token = self.auth_manager.get_cached_token()
        if token:
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            self.authenticated = True

    def get_auth_url(self):
        """Get the Spotify login URL. The user opens this in their browser to authorize the app."""
        self.auth_url = self.auth_manager.get_authorize_url()
        return self.auth_url

    def authenticate_with_code(self, code):
        """Complete authentication using the code from the Spotify redirect URL.

        After the user logs in via the browser, Spotify redirects to our callback URL
        with a code parameter. This method exchanges that code for an access token.
        """
        try:
            self.auth_manager.get_access_token(code)
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            self.authenticated = True
            return True
        except Exception as e:
            print(f'Auth error: {e}')
            return False

    def get_current_track(self):
        """Get info about the currently playing track on Spotify.

        Returns a dict with track name, artist, album, playback status, and album art URL.
        Returns None if nothing is playing or if not authenticated.
        """
        if not self.authenticated:
            return None
        try:
            playback = self.sp.current_playback()
            if playback and playback.get('item'):
                item = playback['item']
                return {
                    'name': item['name'],
                    'artist': ', '.join(a['name'] for a in item['artists']),
                    'album': item['album']['name'],
                    'is_playing': playback['is_playing'],
                    'progress_ms': playback['progress_ms'],      # How far into the track (milliseconds)
                    'duration_ms': item['duration_ms'],           # Total track length (milliseconds)
                    'album_art_url': item['album']['images'][0]['url'] if item['album']['images'] else None,
                }
            return None
        except Exception as e:
            print(f'Playback error: {e}')
            return None

    def play_pause(self):
        """Toggle play/pause on the current Spotify playback."""
        if not self.authenticated:
            return
        try:
            playback = self.sp.current_playback()
            if playback and playback['is_playing']:
                self.sp.pause_playback()
            else:
                self.sp.start_playback()
        except Exception as e:
            print(f'Play/pause error: {e}')

    def next_track(self):
        """Skip to the next track."""
        if not self.authenticated:
            return
        try:
            self.sp.next_track()
        except Exception as e:
            print(f'Next error: {e}')

    def previous_track(self):
        """Go back to the previous track."""
        if not self.authenticated:
            return
        try:
            self.sp.previous_track()
        except Exception as e:
            print(f'Previous error: {e}')
