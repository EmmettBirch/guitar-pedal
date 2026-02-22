# test_tuner.py - Tests for the tuner pitch detection logic
# Tests the pitch detection and frequency-to-note conversion without pygame.

import numpy as np
import sys, os
from math import log2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))

# We can't import TunerScreen directly because it needs pygame.
# Instead, we extract and test the core logic functions independently.

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def detect_pitch(samples, sample_rate=44100, min_amplitude=0.01):
    """Standalone pitch detection extracted from TunerScreen._detect_pitch."""
    if np.max(np.abs(samples)) < min_amplitude:
        return 0.0

    corr = np.correlate(samples, samples, 'full')
    corr = corr[len(corr) // 2:]

    n = len(samples)
    norm = np.arange(n, 0, -1, dtype=np.float64)
    corr = corr / norm
    corr = corr / corr[0]

    min_lag = int(sample_rate / 1200)
    max_lag = int(sample_rate / 27)
    max_lag = min(max_lag, len(corr) - 1)
    if min_lag >= max_lag:
        return 0.0

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

    if 0 < peak_lag < len(corr) - 1:
        s0 = corr[peak_lag - 1]
        s1 = corr[peak_lag]
        s2 = corr[peak_lag + 1]
        denom = s0 - 2 * s1 + s2
        if denom != 0:
            adjustment = (s0 - s2) / (2 * denom)
            peak_lag = peak_lag + adjustment

    if corr[int(round(peak_lag))] < 0.3:
        return 0.0

    return sample_rate / peak_lag


def freq_to_note(freq):
    """Standalone freq-to-note conversion extracted from TunerScreen._freq_to_note."""
    if freq <= 0:
        return ("--", 0.0, 0.0)

    midi = 12 * log2(freq / 440.0) + 69
    midi_rounded = round(midi)

    note_index = midi_rounded % 12
    octave = (midi_rounded // 12) - 1
    note_name = f"{NOTE_NAMES[note_index]}{octave}"

    target_freq = 440.0 * (2 ** ((midi_rounded - 69) / 12.0))
    cents = 1200 * log2(freq / target_freq)

    return (note_name, cents, target_freq)


# -- Pitch Detection Tests -----------------------------------------------

class TestPitchDetection:
    def _make_sine(self, freq, duration=0.1, sample_rate=44100):
        t = np.arange(int(sample_rate * duration)) / sample_rate
        return np.sin(2 * np.pi * freq * t)

    def test_detects_440hz(self):
        samples = self._make_sine(440, duration=0.1)
        detected = detect_pitch(samples)
        assert abs(detected - 440) < 5

    def test_detects_330hz_e4(self):
        samples = self._make_sine(329.63, duration=0.1)
        detected = detect_pitch(samples)
        assert abs(detected - 329.63) < 5

    def test_detects_low_e_82hz(self):
        samples = self._make_sine(82.41, duration=0.15)
        detected = detect_pitch(samples)
        assert abs(detected - 82.41) < 3

    def test_detects_high_e_659hz(self):
        samples = self._make_sine(659.25, duration=0.1)
        detected = detect_pitch(samples)
        assert abs(detected - 659.25) < 10

    def test_silence_returns_zero(self):
        samples = np.zeros(4096)
        assert detect_pitch(samples) == 0.0

    def test_very_quiet_signal_returns_zero(self):
        samples = self._make_sine(440) * 0.001
        assert detect_pitch(samples) == 0.0

    def test_noise_returns_zero_or_unstable(self):
        np.random.seed(42)
        samples = np.random.uniform(-1, 1, 4096)
        # Pure noise should either return 0 or an unreliable frequency
        freq = detect_pitch(samples)
        # We just check it doesn't crash; noise detection is inherently unreliable
        assert isinstance(freq, float)


# -- Frequency to Note Conversion Tests ----------------------------------

class TestFreqToNote:
    def test_a4_is_440(self):
        note, cents, target = freq_to_note(440.0)
        assert note == "A4"
        assert abs(cents) < 0.1
        assert abs(target - 440.0) < 0.01

    def test_a3_is_220(self):
        note, cents, target = freq_to_note(220.0)
        assert note == "A3"
        assert abs(cents) < 0.1

    def test_c4_is_middle_c(self):
        note, cents, target = freq_to_note(261.63)
        assert note == "C4"
        assert abs(cents) < 5

    def test_e2_low_string(self):
        note, cents, target = freq_to_note(82.41)
        assert note == "E2"
        assert abs(cents) < 5

    def test_sharp_note(self):
        # F#4 = 369.99 Hz
        note, cents, target = freq_to_note(369.99)
        assert note == "F#4"
        assert abs(cents) < 5

    def test_slightly_sharp_returns_positive_cents(self):
        # A4 slightly sharp
        note, cents, target = freq_to_note(442.0)
        assert note == "A4"
        assert cents > 0

    def test_slightly_flat_returns_negative_cents(self):
        # A4 slightly flat
        note, cents, target = freq_to_note(438.0)
        assert note == "A4"
        assert cents < 0

    def test_zero_frequency(self):
        note, cents, target = freq_to_note(0)
        assert note == "--"

    def test_negative_frequency(self):
        note, cents, target = freq_to_note(-100)
        assert note == "--"

    def test_cents_within_50_of_nearest_note(self):
        # Any valid frequency should be within 50 cents of nearest note
        for freq in [100, 200, 300, 400, 500, 600, 700, 800]:
            _, cents, _ = freq_to_note(freq)
            assert abs(cents) <= 50
