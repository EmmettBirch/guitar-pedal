# test_project.py - Tests for the Guitar Pedal project
# CS50P Final Project - Emmett Birch (QueenEm)

import json
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))

from project import detect_pitch, freq_to_note, process_effect_chain, snapshot_chain, apply_preset
from effects.overdrive import Overdrive
from effects.fuzz import Fuzz
from effects.chorus import Chorus
from effects.delay import Delay
from effects.reverb import Reverb


def _make_sine(freq, duration=0.1, sample_rate=44100):
    """Helper: generate a sine wave at a given frequency."""
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return np.sin(2 * np.pi * freq * t)


# ========================================================================
# detect_pitch
# ========================================================================

def test_detect_pitch():
    # Detects A4 (440 Hz)
    samples = _make_sine(440, duration=0.1)
    detected = detect_pitch(samples)
    assert abs(detected - 440) < 5

    # Detects E4 (329.63 Hz)
    samples = _make_sine(329.63, duration=0.1)
    detected = detect_pitch(samples)
    assert abs(detected - 329.63) < 5

    # Detects low E2 (82.41 Hz)
    samples = _make_sine(82.41, duration=0.15)
    detected = detect_pitch(samples)
    assert abs(detected - 82.41) < 3

    # Detects high E5 (659.25 Hz)
    samples = _make_sine(659.25, duration=0.1)
    detected = detect_pitch(samples)
    assert abs(detected - 659.25) < 10

    # Silence returns 0
    samples = np.zeros(4096)
    assert detect_pitch(samples) == 0.0

    # Very quiet signal returns 0
    samples = _make_sine(440) * 0.001
    assert detect_pitch(samples) == 0.0

    # Noise does not crash
    np.random.seed(42)
    samples = np.random.uniform(-1, 1, 4096)
    freq = detect_pitch(samples)
    assert isinstance(freq, float)


# ========================================================================
# freq_to_note
# ========================================================================

def test_freq_to_note():
    # A4 = 440 Hz
    note, cents, target = freq_to_note(440.0)
    assert note == "A4"
    assert abs(cents) < 0.1
    assert abs(target - 440.0) < 0.01

    # A3 = 220 Hz
    note, cents, target = freq_to_note(220.0)
    assert note == "A3"
    assert abs(cents) < 0.1

    # C4 (middle C) ~ 261.63 Hz
    note, cents, target = freq_to_note(261.63)
    assert note == "C4"
    assert abs(cents) < 5

    # E2 (low guitar string) ~ 82.41 Hz
    note, cents, target = freq_to_note(82.41)
    assert note == "E2"
    assert abs(cents) < 5

    # F#4 ~ 369.99 Hz
    note, cents, target = freq_to_note(369.99)
    assert note == "F#4"
    assert abs(cents) < 5

    # Slightly sharp A4 returns positive cents
    note, cents, target = freq_to_note(442.0)
    assert note == "A4"
    assert cents > 0

    # Slightly flat A4 returns negative cents
    note, cents, target = freq_to_note(438.0)
    assert note == "A4"
    assert cents < 0

    # Zero and negative frequencies return "--"
    assert freq_to_note(0)[0] == "--"
    assert freq_to_note(-100)[0] == "--"

    # Any valid frequency is within 50 cents of nearest note
    for freq in [100, 200, 300, 400, 500, 600, 700, 800]:
        _, cents, _ = freq_to_note(freq)
        assert abs(cents) <= 50


# ========================================================================
# process_effect_chain
# ========================================================================

def test_process_effect_chain():
    # No effects: passthrough
    samples = np.array([0.0, 0.5, -0.5, 1.0, -1.0])
    result = process_effect_chain(samples.copy(), [])
    np.testing.assert_array_equal(result, samples)

    # Disabled effects are skipped
    od = Overdrive()
    od.enabled = False
    samples = np.array([0.1, 0.2, 0.3])
    result = process_effect_chain(samples.copy(), [od])
    np.testing.assert_array_equal(result, samples)

    # All disabled is passthrough
    effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
    for fx in effects:
        fx.enabled = False
    samples = np.array([0.1, -0.2, 0.3, -0.4, 0.5])
    result = process_effect_chain(samples.copy(), effects)
    np.testing.assert_array_equal(result, samples)

    # Enabled effect modifies signal
    od = Overdrive(gain=10.0)
    od.enabled = True
    samples = np.array([0.5, -0.5, 0.3, -0.3])
    result = process_effect_chain(samples.copy(), [od])
    assert not np.array_equal(result, samples)

    # Output is clipped to [-1, 1]
    od = Overdrive(gain=50.0, level=5.0)
    od.enabled = True
    samples = np.array([1.0, -1.0, 0.8, -0.8])
    result = process_effect_chain(samples, [od])
    assert np.all(result >= -1.0)
    assert np.all(result <= 1.0)

    # Chain order matters
    samples = np.random.uniform(-0.5, 0.5, 512).astype(np.float64)
    result1 = process_effect_chain(samples.copy(),
                                   [Overdrive(gain=8.0), Delay(delay_ms=200, mix=0.5)])
    result2 = process_effect_chain(samples.copy(),
                                   [Delay(delay_ms=200, mix=0.5), Overdrive(gain=8.0)])
    assert not np.array_equal(result1, result2)

    # All five effects together stay in valid range
    effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
    samples = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100)
    result = process_effect_chain(samples.copy(), effects)
    assert result.shape == samples.shape
    assert np.all(result >= -1.0)
    assert np.all(result <= 1.0)


# ========================================================================
# snapshot_chain
# ========================================================================

def test_snapshot_chain():
    # Captures all effects
    effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
    snap = snapshot_chain(effects, "MyPreset")
    assert snap["name"] == "MyPreset"
    assert snap["factory"] is False
    assert "Overdrive" in snap["effects"]
    assert "Fuzz" in snap["effects"]
    assert "Chorus" in snap["effects"]
    assert "Delay" in snap["effects"]
    assert "Reverb" in snap["effects"]

    # Captures enabled state
    od = Overdrive()
    od.enabled = False
    snap = snapshot_chain([od], "Test")
    assert snap["effects"]["Overdrive"]["enabled"] is False

    # Captures parameter values
    od = Overdrive(gain=12.0, tone=0.9, level=0.4)
    snap = snapshot_chain([od], "Test")
    assert snap["effects"]["Overdrive"]["gain"] == 12.0
    assert snap["effects"]["Overdrive"]["tone"] == 0.9
    assert snap["effects"]["Overdrive"]["level"] == 0.4

    # Result is JSON-serializable
    effects = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
    snap = snapshot_chain(effects, "SerTest")
    json.dumps(snap)  # should not raise


# ========================================================================
# apply_preset
# ========================================================================

def test_apply_preset():
    # Sets enabled state
    od = Overdrive()
    od.enabled = True
    preset = {"effects": {"Overdrive": {"enabled": False}}}
    apply_preset([od], preset)
    assert od.enabled is False

    # Sets parameter values
    od = Overdrive(gain=5.0, tone=0.6, level=0.7)
    preset = {"effects": {"Overdrive": {"enabled": True, "gain": 15.0, "tone": 0.3, "level": 0.9}}}
    apply_preset([od], preset)
    assert od.gain == 15.0
    assert od.tone == 0.3
    assert od.level == 0.9

    # Ignores unknown effect names
    od = Overdrive()
    preset = {
        "effects": {
            "Overdrive": {"enabled": True, "gain": 8.0},
            "UnknownFX": {"enabled": True, "param": 42},
        }
    }
    apply_preset([od], preset)
    assert od.gain == 8.0

    # Round trip: snapshot then apply
    effects = [
        Overdrive(gain=12.0, tone=0.8, level=0.5),
        Fuzz(gain=20.0, threshold=0.4, tone=0.7, level=0.8),
        Chorus(rate=2.0, depth=0.008, mix=0.6),
        Delay(delay_ms=400, feedback=0.3, mix=0.4),
        Reverb(room_size=0.6, damping=0.4, mix=0.35),
    ]
    snap = snapshot_chain(effects, "RoundTrip")

    effects2 = [Overdrive(), Fuzz(), Chorus(), Delay(), Reverb()]
    apply_preset(effects2, snap)

    assert effects2[0].gain == 12.0
    assert effects2[1].threshold == 0.4
    assert effects2[2].rate == 2.0
    assert effects2[3].delay_ms == 400
    assert effects2[4].room_size == 0.6
