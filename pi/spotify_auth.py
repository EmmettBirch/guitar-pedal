# spotify_auth.py - Helper script to authenticate with Spotify
# Run this on the Pi to connect your Spotify account.
#
# Usage:
#   Step 1: Run without arguments to get the login URL
#       python3 spotify_auth.py
#
#   Step 2: Open the URL in your browser, log in, and copy the redirect URL
#
#   Step 3: Run again with the redirect URL to complete authentication
#       python3 spotify_auth.py "http://127.0.0.1:8888/callback?code=..."

import sys

# Add the pi directory to the Python path so we can import our modules
sys.path.insert(0, '/home/emmett/guitar-pedal/pi')
from comms.spotify_client import SpotifyClient

# Create a Spotify client (will automatically use cached token if available)
client = SpotifyClient()

if client.authenticated:
    # Already logged in - show what's playing as a test
    print("Already authenticated!")
    track = client.get_current_track()
    if track:
        print(f"Now playing: {track['name']} - {track['artist']}")
    else:
        print("Nothing playing right now")
elif len(sys.argv) > 1:
    # A redirect URL was provided - extract the auth code and complete login
    url = sys.argv[1]
    code = client.auth_manager.parse_response_code(url)
    if client.authenticate_with_code(code):
        print("Authenticated successfully!")
    else:
        print("Authentication failed")
else:
    # No arguments - show the login URL
    url = client.get_auth_url()
    print(f"Open this URL in your browser:\n\n{url}\n")
    print("Then run: python3 ~/guitar-pedal/pi/spotify_auth.py <redirect_url>")
