# mock_signal.py - Generates a fake guitar signal for testing without the Daisy hardware.
# Produces a continuous sine wave at 440Hz (concert A) that can be used
# as input to the effect chain and visualiser. Once the Daisy is connected,
# this will be replaced by real audio input over serial.

import numpy as np


class MockSignal:
    def __init__(self, frequency=440, sample_rate=44100):
        self.frequency = frequency      # Frequency in Hz (440 = A4 note)
        self.sample_rate = sample_rate   # Samples per second
        self.phase = 0.0                 # Current phase position in the wave

    def get_samples(self, n):
        """Generate n samples of a sine wave in the range [-1.0, 1.0].

        Maintains phase continuity so consecutive calls produce a seamless
        waveform — calling get_samples(512) twice gives the same result
        as calling get_samples(1024) once.

        Args:
            n: Number of samples to generate

        Returns:
            numpy float64 array of n samples in [-1.0, 1.0]
        """
        # Create an array of time points for each sample
        t = (self.phase + np.arange(n)) / self.sample_rate

        # Generate the sine wave: sin(2π * frequency * time)
        samples = np.sin(2 * np.pi * self.frequency * t)

        # Advance the phase for the next call.
        # Modulo keeps it from growing to infinity over long sessions.
        self.phase = (self.phase + n) % self.sample_rate

        return samples
