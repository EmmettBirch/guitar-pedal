# main.py - Entry point for the Guitar Pedal application
# This is the main loop that controls which screen is shown on the LCD display.
# It handles switching between the idle animation, the menu, and sub-screens like Spotify.

import pygame
import sys

from ui.idle_screen import IdleScreen
from ui.menu import Menu
from ui.spotify_screen import SpotifyScreen
from comms.spotify_client import SpotifyClient

# App states - these control which screen is currently being displayed
STATE_IDLE = "idle"         # Idle animation with waveforms
STATE_MENU = "menu"         # Main menu with options
STATE_SPOTIFY = "spotify"   # Spotify now playing screen


def main():
    # Initialise pygame (the library we use to draw graphics on screen)
    pygame.init()

    # Create a fullscreen display and hide the mouse cursor
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Guitar Pedal")
    pygame.mouse.set_visible(False)

    # Clock controls the frame rate (60 FPS)
    clock = pygame.time.Clock()

    # Create all our screen objects
    idle = IdleScreen(screen)               # The idle animation screen
    menu = Menu(screen)                     # The main menu screen
    spotify_client = SpotifyClient()        # Handles Spotify API communication
    spotify_screen = SpotifyScreen(screen, spotify_client)  # Spotify UI screen

    # Start on the idle screen
    state = STATE_IDLE

    # Main game loop - runs 60 times per second until we exit
    running = True
    while running:
        # dt = time since last frame in seconds, used to keep animations smooth
        dt = clock.tick(60) / 1000.0

        # Process all events (taps, key presses, etc.)
        for event in pygame.event.get():
            # Window close event
            if event.type == pygame.QUIT:
                running = False

            # Escape key - go back to idle, or exit if already on idle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if state in (STATE_MENU, STATE_SPOTIFY):
                    state = STATE_IDLE
                else:
                    running = False

            # Handle events based on which screen we're on
            if state == STATE_IDLE:
                # Tap anywhere on the idle screen to open the menu
                if event.type == pygame.MOUSEBUTTONDOWN:
                    state = STATE_MENU
                    menu.selected = None    # Reset menu selection

            elif state == STATE_MENU:
                # Pass the event to the menu and check if something was selected
                selection = menu.handle_event(event)
                if selection == "Spotify":
                    state = STATE_SPOTIFY   # Open Spotify screen
                elif selection == "Exit":
                    running = False         # Close the app
                elif selection:
                    # Other menu items aren't implemented yet
                    print(f"Selected: {selection}")

            elif state == STATE_SPOTIFY:
                # Pass the event to the Spotify screen
                result = spotify_screen.handle_event(event)
                if result == "back":
                    state = STATE_MENU      # Go back to the menu
                    menu.selected = None

        # Draw the current screen
        if state == STATE_IDLE:
            idle.draw(dt)
        elif state == STATE_MENU:
            menu.draw(dt)
        elif state == STATE_SPOTIFY:
            spotify_screen.draw(dt)

        # Update the display with everything we just drew
        pygame.display.flip()

    # Clean up and exit
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
