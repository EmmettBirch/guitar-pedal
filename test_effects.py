# test_effects.py - Tests for individual audio effects

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))

from effects.overdrive import Overdrive
from effects.fuzz import Fuzz
from effects.chorus import Chorus
from effects.delay import Delay
from effects.reverb import Reverb


# -- Overdrive -----------------------------------------------------------

class TestOverdriveInit:
    def test_default_params(self):
        od = Overdrive()
        assert od.gain == 5.0
        assert od.tone == 0.6
        assert od.level == 0.7
        assert od.enabled is True

    def test_custom_params(self):
        od = Overdrive(gain=10.0, tone=0.8, level=0.5)
        assert od.gain == 10.0
        assert od.tone == 0.8
        assert od.level == 0.5


class TestOverdriveProcess:
    def test_output_shape_matches_input(self):
        od = Overdrive()
        samples = np.random.uniform(-1, 1, 512)
        result = od.process(samples)
        assert result.shape == samples.shape

    def test_soft_clips_loud_signal(self):
        od = Overdrive(gain=20.0, level=1.0)
        samples = np.ones(100)
        result = od.process(samples)
        assert np.all(np.abs(result) <= 1.0)

    def test_silence_produces_near_silence(self):
        od = Overdrive()
        samples = np.zeros(256)
        result = od.process(samples)
        assert np.max(np.abs(result)) < 0.01

    def test_higher_gain_changes_output(self):
        samples = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100)
        od_low = Overdrive(gain=2.0, tone=1.0, level=1.0)
        od_high = Overdrive(gain=20.0, tone=1.0, level=1.0)
        result_low = od_low.process(samples.copy())
        result_high = od_high.process(samples.copy())
        # Different gain settings should produce different outputs
        assert not np.allclose(result_low, result_high)


# -- Fuzz ----------------------------------------------------------------

class TestFuzzInit:
    def test_default_params(self):
        fz = Fuzz()
        assert fz.gain == 15.0
        assert fz.threshold == 0.3
        assert fz.tone == 0.5
        assert fz.level == 0.6
        assert fz.enabled is True


class TestFuzzProcess:
    def test_output_shape_matches_input(self):
        fz = Fuzz()
        samples = np.random.uniform(-1, 1, 512)
        result = fz.process(samples)
        assert result.shape == samples.shape

    def test_hard_clips_signal(self):
        fz = Fuzz(gain=30.0, threshold=0.2, level=1.0)
        samples = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100)
        result = fz.process(samples)
        assert np.all(np.abs(result) <= 1.1)

    def test_silence_produces_near_silence(self):
        fz = Fuzz()
        samples = np.zeros(256)
        result = fz.process(samples)
        assert np.max(np.abs(result)) < 0.01

    def test_asymmetric_clipping(self):
        fz = Fuzz(gain=20.0, threshold=0.3, tone=1.0, level=1.0)
        samples = np.sin(2 * np.pi * 100 * np.arange(4096) / 44100)
        result = fz.process(samples)
        pos_max = np.max(result)
        neg_max = np.abs(np.min(result))
        # Negative threshold is 1.5x positive, so negative peaks can be larger
        assert neg_max >= pos_max * 0.9


# -- Chorus --------------------------------------------------------------

class TestChorusInit:
    def test_default_params(self):
        ch = Chorus()
        assert ch.rate == 1.5
        assert ch.depth == 0.005
        assert ch.mix == 0.5
        assert ch.enabled is True


class TestChorusProcess:
    def test_output_shape_matches_input(self):
        ch = Chorus()
        samples = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100)
        result = ch.process(samples)
        assert result.shape == samples.shape

    def test_zero_mix_returns_dry_signal(self):
        ch = Chorus(mix=0.0)
        samples = np.sin(2 * np.pi * 440 * np.arange(512) / 44100)
        result = ch.process(samples.copy())
        np.testing.assert_allclose(result, samples, atol=1e-10)

    def test_chorus_modifies_signal(self):
        ch = Chorus(rate=2.0, depth=0.005, mix=0.5)
        samples = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100)
        result = ch.process(samples.copy())
        assert not np.allclose(result, samples)

    def test_lfo_phase_wraps(self):
        ch = Chorus()
        samples = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)
        ch.process(samples)
        assert 0 <= ch._lfo_phase < 2 * np.pi


# -- Delay ---------------------------------------------------------------

class TestDelayInit:
    def test_default_params(self):
        dl = Delay()
        assert dl.delay_ms == 350
        assert dl.feedback == 0.4
        assert dl.mix == 0.5
        assert dl.enabled is True


class TestDelayProcess:
    def test_output_shape_matches_input(self):
        dl = Delay()
        samples = np.random.uniform(-1, 1, 512)
        result = dl.process(samples)
        assert result.shape == samples.shape

    def test_zero_mix_returns_dry_signal(self):
        dl = Delay(mix=0.0)
        samples = np.sin(2 * np.pi * 440 * np.arange(512) / 44100)
        result = dl.process(samples.copy())
        np.testing.assert_allclose(result, samples, atol=1e-10)

    def test_echo_appears_after_delay_time(self):
        dl = Delay(delay_ms=100, feedback=0.5, mix=1.0, sample_rate=44100)
        samples = np.zeros(44100)
        samples[0] = 1.0
        result = dl.process(samples)
        delay_samples = int(0.1 * 44100)
        assert abs(result[delay_samples]) > 0.1

    def test_silence_produces_silence(self):
        dl = Delay()
        samples = np.zeros(512)
        result = dl.process(samples)
        np.testing.assert_array_equal(result, np.zeros(512))

    def test_feedback_creates_repeating_echoes(self):
        dl = Delay(delay_ms=100, feedback=0.5, mix=1.0, sample_rate=44100)
        samples = np.zeros(44100)
        samples[0] = 1.0
        result = dl.process(samples)
        delay_samples = int(0.1 * 44100)
        first_echo = abs(result[delay_samples])
        second_echo = abs(result[delay_samples * 2])
        assert first_echo > second_echo > 0


# -- Reverb --------------------------------------------------------------

class TestReverbInit:
    def test_default_params(self):
        rv = Reverb()
        assert rv.room_size == 0.7
        assert rv.damping == 0.5
        assert rv.mix == 0.3
        assert rv.enabled is True

    def test_has_comb_and_allpass_filters(self):
        rv = Reverb()
        assert len(rv._combs) == 4
        assert len(rv._allpasses) == 2


class TestReverbProcess:
    def test_output_shape_matches_input(self):
        rv = Reverb()
        samples = np.random.uniform(-1, 1, 512)
        result = rv.process(samples)
        assert result.shape == samples.shape

    def test_zero_mix_returns_dry_signal(self):
        rv = Reverb(mix=0.0)
        samples = np.sin(2 * np.pi * 440 * np.arange(512) / 44100)
        result = rv.process(samples.copy())
        np.testing.assert_allclose(result, samples, atol=1e-10)

    def test_reverb_adds_tail(self):
        rv = Reverb(room_size=0.7, mix=1.0)
        samples = np.zeros(4096)
        samples[0] = 1.0
        result = rv.process(samples)
        tail_energy = np.sum(result[100:] ** 2)
        assert tail_energy > 0.01

    def test_silence_produces_silence(self):
        rv = Reverb()
        samples = np.zeros(512)
        result = rv.process(samples)
        assert np.max(np.abs(result)) < 1e-10
