import numpy as np


class Delay:
    """Echo effect using a circular buffer with feedback."""

    def __init__(self, delay_ms=350, feedback=0.4, mix=0.5, sample_rate=44100):
        self.enabled = True
        self.delay_ms = delay_ms
        self.feedback = feedback
        self.mix = mix
        self.sample_rate = sample_rate

        # Circular buffer: 2 seconds max
        max_samples = sample_rate * 2
        self._buffer = np.zeros(max_samples, dtype=np.float64)
        self._write_pos = 0

    def process(self, samples):
        delay_samples = int(self.delay_ms / 1000.0 * self.sample_rate)
        buf = self._buffer
        buf_len = len(buf)
        wp = self._write_pos
        out = np.empty_like(samples)

        for i in range(len(samples)):
            # Read from the delay line
            read_pos = (wp - delay_samples) % buf_len
            delayed = buf[read_pos]

            # Mix dry and wet
            out[i] = samples[i] * (1.0 - self.mix) + delayed * self.mix

            # Write input + feedback into buffer
            buf[wp] = samples[i] + delayed * self.feedback

            # Advance write pointer
            wp = (wp + 1) % buf_len

        self._write_pos = wp
        return out
