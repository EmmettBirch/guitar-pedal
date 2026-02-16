# project.py - Guitar Pedal: a digital guitar effects pedal
# built with a Raspberry Pi 4 and an Electrosmith Daisy.
#
# CS50P Final Project
# Emmett Birch (QueenEm)

import sys
import os
import numpy as np
from math import log2

# Add the pi/ directory to the path so we can import the app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Maps effect class names to the parameter attributes we serialize.
EFFECT_PARAMS = {
    'Overdrive': ['gain', 'tone', 'level'],
    'Fuzz':      ['gain', 'threshold', 'tone', 'level'],
    'Chorus':    ['rate', 'depth', 'mix'],
    'Delay':     ['delay_ms', 'feedback', 'mix'],
    'Reverb':    ['room_size', 'damping', 'mix'],
}


def main():
    """Launch the Guitar Pedal application.

    Initialises pygame, creates all screen objects, and runs the main event
    loop at 60 FPS. Handles state transitions between screens via touch
    events and keyboard input (Escape to go back, tap to navigate).
    """
    # Imports are inside main() so pytest can import project.py without
    # needing pygame or Spotify credentials installed.
    import pygame
    from ui.idle_screen import IdleScreen
    from ui.menu import Menu
    from ui.spotify_screen import SpotifyScreen
    from ui.visualiser import Visualiser
    from ui.effects_screen import EffectsScreen
    from ui.effect_chain_screen import EffectChainScreen
    from ui.tuner import TunerScreen
    from ui.presets_screen import PresetsScreen
    from comms.spotify_client import SpotifyClient
    from comms.mock_signal import MockSignal
    from effects.effect_chain import EffectChain
    from effects import Overdrive, Fuzz, Chorus, Delay, Reverb

    # App states — these control which screen is currently displayed
    STATE_IDLE = "idle"
    STATE_MENU = "menu"
    STATE_SPOTIFY = "spotify"
    STATE_VISUALISER = "visualiser"
    STATE_EFFECTS = "effects"
    STATE_CHAIN = "effect_chain"
    STATE_TUNER = "tuner"
    STATE_PRESETS = "presets"

    # Initialise pygame and create a fullscreen display
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Guitar Pedal")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    # Create shared signal source and effect chain
    mock_signal = MockSignal()
    effect_chain = EffectChain()

    # Create the five audio effects and load them into the chain
    overdrive = Overdrive()
    fuzz = Fuzz()
    chorus = Chorus()
    delay = Delay()
    reverb = Reverb()
    effect_chain.effects = [overdrive, fuzz, chorus, delay, reverb]

    # Create all screen objects
    idle = IdleScreen(screen)
    menu = Menu(screen)
    spotify_client = SpotifyClient()
    spotify_screen = SpotifyScreen(screen, spotify_client)
    visualiser = Visualiser(screen, mock_signal, effect_chain)
    effects_screen = EffectsScreen(screen, effect_chain)
    chain_screen = EffectChainScreen(screen, effect_chain)
    tuner_screen = TunerScreen(screen, mock_signal)
    presets_screen = PresetsScreen(screen, effect_chain)

    # Start on the idle screen
    state = STATE_IDLE
    running = True

    # Main loop — runs at 60 FPS until the user exits
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds

        # Process all events (taps, key presses, etc.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Escape key: go back to idle, or exit if already on idle
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if state in (STATE_MENU, STATE_SPOTIFY, STATE_VISUALISER,
                             STATE_EFFECTS, STATE_CHAIN, STATE_TUNER,
                             STATE_PRESETS):
                    state = STATE_IDLE
                else:
                    running = False

            # Route events to the current screen
            if state == STATE_IDLE:
                # Tap anywhere on the idle screen to open the menu
                if event.type == pygame.MOUSEBUTTONDOWN:
                    state = STATE_MENU
                    menu.selected = None

            elif state == STATE_MENU:
                # Menu returns the label of the selected item
                selection = menu.handle_event(event)
                if selection == "Spotify":
                    state = STATE_SPOTIFY
                elif selection == "Visualiser":
                    state = STATE_VISUALISER
                elif selection == "Effects":
                    state = STATE_EFFECTS
                    effects_screen.view = 'list'
                elif selection == "Effect Chain":
                    state = STATE_CHAIN
                elif selection == "Tuner":
                    state = STATE_TUNER
                elif selection == "Presets":
                    state = STATE_PRESETS
                    presets_screen.refresh_presets()
                    presets_screen.view = 'list'
                elif selection == "Exit":
                    running = False

            elif state == STATE_SPOTIFY:
                result = spotify_screen.handle_event(event)
                if result == "back":
                    state = STATE_MENU
                    menu.selected = None

            elif state == STATE_VISUALISER:
                result = visualiser.handle_event(event)
                if result == "back":
                    state = STATE_MENU
                    menu.selected = None

            elif state == STATE_EFFECTS:
                result = effects_screen.handle_event(event)
                if result == "back":
                    state = STATE_MENU
                    menu.selected = None

            elif state == STATE_CHAIN:
                result = chain_screen.handle_event(event)
                if result == "back":
                    state = STATE_MENU
                    menu.selected = None

            elif state == STATE_TUNER:
                result = tuner_screen.handle_event(event)
                if result == "back":
                    state = STATE_MENU
                    menu.selected = None

            elif state == STATE_PRESETS:
                result = presets_screen.handle_event(event)
                if result == "back":
                    state = STATE_MENU
                    menu.selected = None

        # Draw the current screen
        if state == STATE_IDLE:
            idle.draw(dt)
        elif state == STATE_MENU:
            menu.draw(dt)
        elif state == STATE_SPOTIFY:
            spotify_screen.draw(dt)
        elif state == STATE_VISUALISER:
            visualiser.draw(dt)
        elif state == STATE_EFFECTS:
            effects_screen.draw(dt)
        elif state == STATE_CHAIN:
            chain_screen.draw(dt)
        elif state == STATE_TUNER:
            tuner_screen.draw(dt)
        elif state == STATE_PRESETS:
            presets_screen.draw(dt)

        # Update the display with everything we just drew
        pygame.display.flip()

    # Clean up and exit
    pygame.quit()
    sys.exit()


def detect_pitch(samples, sample_rate=44100, min_amplitude=0.01):
    """Detect the fundamental pitch of an audio signal using autocorrelation.

    Analyses a buffer of audio samples and returns the detected fundamental
    frequency in Hz, or 0.0 if no clear pitch is found. Uses normalised
    autocorrelation with parabolic interpolation for sub-sample accuracy.

    Args:
        samples:       numpy array of audio samples (float64, typically [-1.0, 1.0])
        sample_rate:   sample rate in Hz (default 44100)
        min_amplitude: minimum signal level required to attempt detection

    Returns:
        Detected frequency in Hz, or 0.0 if no pitch found.
    """
    if np.max(np.abs(samples)) < min_amplitude:
        return 0.0

    # Autocorrelation via numpy — take the second half (positive lags)
    corr = np.correlate(samples, samples, 'full')
    corr = corr[len(corr) // 2:]

    # Normalise per-lag to correct for decreasing overlap at higher lags
    n = len(samples)
    norm = np.arange(n, 0, -1, dtype=np.float64)
    corr = corr / norm
    corr = corr / corr[0]

    # Search range: ~27 Hz (low E guitar) to ~1200 Hz
    min_lag = int(sample_rate / 1200)
    max_lag = int(sample_rate / 27)
    max_lag = min(max_lag, len(corr) - 1)
    if min_lag >= max_lag:
        return 0.0

    # Find the first positive peak after the correlation dips below zero
    search = corr[min_lag:max_lag]
    below_zero = np.where(search < 0)[0]
    if len(below_zero) == 0:
        return 0.0

    start = below_zero[0]
    remaining = search[start:]
    above_zero = np.where(remaining > 0)[0]
    if len(above_zero) == 0:
        return 0.0

    pos_start = start + above_zero[0]
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

    # Require minimum correlation strength
    if corr[int(round(peak_lag))] < 0.3:
        return 0.0

    return sample_rate / peak_lag


def freq_to_note(freq):
    """Convert a frequency in Hz to the nearest chromatic note name with cents offset.

    Uses A4 = 440 Hz as the reference pitch. Returns the note name with octave
    number (e.g. 'A4', 'C#3'), the cents offset from the target pitch (positive
    means sharp, negative means flat), and the exact frequency of the target note.

    Args:
        freq: frequency in Hz (must be > 0 for a valid result)

    Returns:
        Tuple of (note_name, cents_offset, target_frequency).
        Returns ('--', 0.0, 0.0) if freq <= 0.
    """
    if freq <= 0:
        return ("--", 0.0, 0.0)

    # MIDI note number (69 = A4 = 440 Hz)
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


def process_effect_chain(samples, effects):
    """Run audio samples through an ordered list of effects.

    Each enabled effect processes the samples in sequence. Disabled effects
    are skipped. The output is clipped to [-1.0, 1.0] to prevent digital
    distortion beyond the valid audio range.

    Each effect must have:
      - effect.enabled (bool): whether the effect is active
      - effect.process(samples): takes and returns a numpy array

    Args:
        samples: numpy array of audio samples (float64)
        effects: list of effect objects to process through in order

    Returns:
        numpy array of processed samples, clipped to [-1.0, 1.0]
    """
    for effect in effects:
        if effect.enabled:
            samples = effect.process(samples)
    return np.clip(samples, -1.0, 1.0)


def snapshot_chain(effects, name):
    """Capture the current state of a list of effects as a preset dictionary.

    Iterates through each effect, records its enabled state and all registered
    parameters, and returns a dictionary that can be serialized to JSON and
    later restored with apply_preset().

    Args:
        effects: list of effect objects to snapshot
        name:    name for the preset

    Returns:
        Dict with keys 'name', 'factory' (False), and 'effects' (a dict
        mapping effect class names to their parameter values).
    """
    effects_data = {}
    for fx in effects:
        class_name = type(fx).__name__
        params = EFFECT_PARAMS.get(class_name, [])
        entry = {"enabled": fx.enabled}
        for attr in params:
            entry[attr] = getattr(fx, attr)
        effects_data[class_name] = entry
    return {"name": name, "factory": False, "effects": effects_data}


def apply_preset(effects, preset):
    """Apply a preset dictionary to a list of effects.

    Sets the enabled state and parameter values for each effect that appears
    in both the preset and the effects list. Effects not mentioned in the
    preset are left unchanged. Unknown effect names in the preset are ignored.

    Args:
        effects: list of effect objects to modify
        preset:  dict with an 'effects' key mapping class names to param dicts
    """
    effects_data = preset.get("effects", {})
    for fx in effects:
        class_name = type(fx).__name__
        if class_name in effects_data:
            data = effects_data[class_name]
            fx.enabled = data.get("enabled", fx.enabled)
            for attr in EFFECT_PARAMS.get(class_name, []):
                if attr in data:
                    setattr(fx, attr, data[attr])


if __name__ == "__main__":
    main()
