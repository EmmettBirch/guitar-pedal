import numpy as np


class Chorus:
    """Modulated delay line chorus effect with sine LFO."""

    def __init__(self, rate=1.5, depth=0.005, mix=0.5, sample_rate=44100):
        self.enabled = True
        self.rate = rate        # LFO frequency in Hz
        self.depth = depth      # Modulation depth in seconds
        self.mix = mix
        self.sample_rate = sample_rate

        # Base delay ~7ms plus enough room for modulation
        self._base_delay = int(0.007 * sample_rate)
        max_delay = self._base_delay + int(depth * sample_rate) + 2
        self._buffer = np.zeros(max_delay + sample_rate, dtype=np.float64)
        self._write_pos = 0
        self._lfo_phase = 0.0

    def process(self, samples):
        buf = self._buffer
        buf_len = len(buf)
        wp = self._write_pos
        phase = self._lfo_phase
        phase_inc = 2.0 * np.pi * self.rate / self.sample_rate
        depth_samples = self.depth * self.sample_rate
        base = self._base_delay
        out = np.empty_like(samples)

        for i in range(len(samples)):
            # Write current sample into buffer
            buf[wp] = samples[i]

            # LFO modulates the delay length
            mod = np.sin(phase) * depth_samples
            delay = base + mod

            # Fractional delay with linear interpolation
            read_pos = wp - delay
            read_idx = int(np.floor(read_pos))
            frac = read_pos - read_idx
            idx0 = read_idx % buf_len
            idx1 = (read_idx + 1) % buf_len
            delayed = buf[idx0] * (1.0 - frac) + buf[idx1] * frac

            # Mix dry and wet
            out[i] = samples[i] * (1.0 - self.mix) + delayed * self.mix

            # Advance
            wp = (wp + 1) % buf_len
            phase += phase_inc

        # Keep phase from growing unbounded
        self._lfo_phase = phase % (2.0 * np.pi)
        self._write_pos = wp
        return out
