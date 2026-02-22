# test_mock_signal.py - Tests for the MockSignal generator

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi'))

from comms.mock_signal import MockSignal


class TestMockSignalInit:
    def test_default_frequency(self):
        sig = MockSignal()
        assert sig.frequency == 440

    def test_default_sample_rate(self):
        sig = MockSignal()
        assert sig.sample_rate == 44100

    def test_custom_frequency(self):
        sig = MockSignal(frequency=880)
        assert sig.frequency == 880

    def test_custom_sample_rate(self):
        sig = MockSignal(sample_rate=48000)
        assert sig.sample_rate == 48000

    def test_initial_phase_is_zero(self):
        sig = MockSignal()
        assert sig.phase == 0.0


class TestMockSignalOutput:
    def test_returns_correct_number_of_samples(self):
        sig = MockSignal()
        samples = sig.get_samples(512)
        assert len(samples) == 512

    def test_returns_numpy_array(self):
        sig = MockSignal()
        samples = sig.get_samples(100)
        assert isinstance(samples, np.ndarray)

    def test_samples_in_range(self):
        sig = MockSignal()
        samples = sig.get_samples(44100)
        assert np.all(samples >= -1.0)
        assert np.all(samples <= 1.0)

    def test_single_sample(self):
        sig = MockSignal()
        samples = sig.get_samples(1)
        assert len(samples) == 1

    def test_zero_samples(self):
        sig = MockSignal()
        samples = sig.get_samples(0)
        assert len(samples) == 0


class TestMockSignalPhaseContinuity:
    def test_phase_advances(self):
        sig = MockSignal()
        sig.get_samples(100)
        assert sig.phase != 0.0

    def test_consecutive_calls_are_continuous(self):
        sig1 = MockSignal(frequency=440)
        combined = sig1.get_samples(1024)

        sig2 = MockSignal(frequency=440)
        part1 = sig2.get_samples(512)
        part2 = sig2.get_samples(512)
        split_combined = np.concatenate([part1, part2])

        np.testing.assert_allclose(combined, split_combined, atol=1e-10)

    def test_phase_wraps(self):
        sig = MockSignal(sample_rate=44100)
        sig.get_samples(44100)
        assert sig.phase < sig.sample_rate


class TestMockSignalFrequency:
    def test_correct_frequency_via_zero_crossings(self):
        sig = MockSignal(frequency=440, sample_rate=44100)
        samples = sig.get_samples(44100)
        crossings = np.sum(np.diff(np.sign(samples)) != 0)
        # A 440Hz sine wave has ~880 zero crossings per second
        expected = 440 * 2
        assert abs(crossings - expected) <= 2
